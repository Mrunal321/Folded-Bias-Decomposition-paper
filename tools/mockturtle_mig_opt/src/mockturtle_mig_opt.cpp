#include <cstdlib>
#include <iostream>
#include <optional>
#include <string>
#include <vector>

#include <lorina/blif.hpp>
#include <mockturtle/algorithms/cleanup.hpp>
#include <mockturtle/algorithms/mig_algebraic_rewriting.hpp>
#include <mockturtle/algorithms/mig_resub.hpp>
#include <mockturtle/algorithms/node_resynthesis.hpp>
#include <mockturtle/algorithms/node_resynthesis/mig_npn.hpp>
#include <mockturtle/io/blif_reader.hpp>
#include <mockturtle/io/write_blif.hpp>
#include <mockturtle/networks/klut.hpp>
#include <mockturtle/networks/mig.hpp>
#include <mockturtle/views/depth_view.hpp>
#include <mockturtle/views/fanout_view.hpp>

namespace {

struct options
{
  std::string input_blif;
  std::optional<std::string> output_blif;
  uint32_t rounds = 3u;
  uint32_t max_pis = 8u;
  uint32_t max_inserts = 1u;
  bool until_stable = true;
  std::string recipe = "resub";
};

void print_usage( const char* argv0 )
{
  std::cerr
      << "Usage: " << argv0 << " --input <file.blif> [options]\n"
      << "Options:\n"
      << "  --output <file.blif>      Write optimized MIG as BLIF\n"
      << "  --rounds <n>              Max resub rounds (default: 3)\n"
      << "  --max-pis <n>             resub max_pis (default: 8)\n"
      << "  --max-inserts <n>         resub max_inserts (default: 1)\n"
      << "  --recipe <name>           One of: resub|resub2|depth_resub2|resub_depth_resub2\n"
      << "  --no-until-stable         Run all rounds even without improvement\n"
      << "  --help                    Show this help message\n";
}

bool parse_uint( const std::string& s, uint32_t& out )
{
  char* end = nullptr;
  const unsigned long val = std::strtoul( s.c_str(), &end, 10 );
  if ( end == nullptr || *end != '\0' )
  {
    return false;
  }
  out = static_cast<uint32_t>( val );
  return true;
}

bool parse_args( int argc, char** argv, options& opt )
{
  if ( argc <= 1 )
  {
    print_usage( argv[0] );
    return false;
  }

  for ( int i = 1; i < argc; ++i )
  {
    const std::string a = argv[i];
    if ( a == "--help" || a == "-h" )
    {
      print_usage( argv[0] );
      return false;
    }
    if ( a == "--input" )
    {
      if ( i + 1 >= argc )
      {
        std::cerr << "Missing value for --input\n";
        return false;
      }
      opt.input_blif = argv[++i];
      continue;
    }
    if ( a == "--output" )
    {
      if ( i + 1 >= argc )
      {
        std::cerr << "Missing value for --output\n";
        return false;
      }
      opt.output_blif = std::string{ argv[++i] };
      continue;
    }
    if ( a == "--rounds" )
    {
      if ( i + 1 >= argc || !parse_uint( argv[i + 1], opt.rounds ) )
      {
        std::cerr << "Invalid value for --rounds\n";
        return false;
      }
      ++i;
      continue;
    }
    if ( a == "--max-pis" )
    {
      if ( i + 1 >= argc || !parse_uint( argv[i + 1], opt.max_pis ) )
      {
        std::cerr << "Invalid value for --max-pis\n";
        return false;
      }
      ++i;
      continue;
    }
    if ( a == "--max-inserts" )
    {
      if ( i + 1 >= argc || !parse_uint( argv[i + 1], opt.max_inserts ) )
      {
        std::cerr << "Invalid value for --max-inserts\n";
        return false;
      }
      ++i;
      continue;
    }
    if ( a == "--no-until-stable" )
    {
      opt.until_stable = false;
      continue;
    }
    if ( a == "--recipe" )
    {
      if ( i + 1 >= argc )
      {
        std::cerr << "Missing value for --recipe\n";
        return false;
      }
      opt.recipe = argv[++i];
      if ( opt.recipe != "resub" && opt.recipe != "resub2" &&
           opt.recipe != "depth_resub2" && opt.recipe != "resub_depth_resub2" )
      {
        std::cerr << "Unsupported recipe: " << opt.recipe << "\n";
        return false;
      }
      continue;
    }

    std::cerr << "Unknown argument: " << a << "\n";
    return false;
  }

  if ( opt.input_blif.empty() )
  {
    std::cerr << "Missing required --input argument\n";
    return false;
  }

  return true;
}

} // namespace

int main( int argc, char** argv )
{
  using namespace mockturtle;

  options opt;
  if ( !parse_args( argc, argv, opt ) )
  {
    return 1;
  }

  klut_network klut;
  if ( lorina::read_blif( opt.input_blif, blif_reader( klut ) ) != lorina::return_code::success )
  {
    std::cerr << "Failed to read BLIF: " << opt.input_blif << "\n";
    return 2;
  }

  mig_npn_resynthesis resyn;
  mig_network mig = node_resynthesis<mig_network>( klut, resyn );
  mig = cleanup_dangling( mig );

  const uint32_t mig_before = mig.num_gates();
  const uint32_t depth_before = depth_view{ mig }.depth();
  uint32_t rounds_run = 0u;

  resubstitution_params ps;
  ps.max_pis = opt.max_pis;
  ps.max_inserts = opt.max_inserts;
  ps.progress = false;

  auto run_resub_rounds = [&]( bool use_resub2 ) {
    for ( uint32_t i = 0u; i < opt.rounds; ++i )
    {
      const auto before_round = mig.num_gates();

      depth_view depth_mig{ mig };
      fanout_view fanout_mig{ depth_mig };

      resubstitution_stats st;
      if ( use_resub2 )
      {
        mig_resubstitution2( fanout_mig, ps, &st );
      }
      else
      {
        mig_resubstitution( fanout_mig, ps, &st );
      }
      mig = cleanup_dangling( mig );

      ++rounds_run;
      const auto after_round = mig.num_gates();
      if ( opt.until_stable && after_round >= before_round )
      {
        break;
      }
    }
  };

  auto run_depth_rewrite = [&]() {
    depth_view depth_mig{ mig };
    mig_algebraic_depth_rewriting_params dps;
    dps.strategy = mig_algebraic_depth_rewriting_params::aggressive;
    dps.allow_area_increase = false;
    mig_algebraic_depth_rewriting_stats dst;
    mig_algebraic_depth_rewriting( depth_mig, dps, &dst );
    mig = cleanup_dangling( mig );
  };

  if ( opt.recipe == "resub" )
  {
    run_resub_rounds( false );
  }
  else if ( opt.recipe == "resub2" )
  {
    run_resub_rounds( true );
  }
  else if ( opt.recipe == "depth_resub2" )
  {
    run_depth_rewrite();
    run_resub_rounds( true );
  }
  else if ( opt.recipe == "resub_depth_resub2" )
  {
    run_resub_rounds( false );
    run_depth_rewrite();
    run_resub_rounds( true );
  }

  if ( opt.output_blif.has_value() )
  {
    write_blif( mig, *opt.output_blif );
  }

  std::cout << "RESULT"
            << " klut_gates=" << klut.num_gates()
            << " mig_before=" << mig_before
            << " mig_after=" << mig.num_gates()
            << " depth_before=" << depth_before
            << " depth_after=" << depth_view{ mig }.depth()
            << " rounds=" << rounds_run
            << " max_pis=" << opt.max_pis
            << " max_inserts=" << opt.max_inserts
            << " recipe=" << opt.recipe
            << "\n";

  return 0;
}
