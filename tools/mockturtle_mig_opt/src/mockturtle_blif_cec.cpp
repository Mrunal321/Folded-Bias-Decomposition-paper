#include <iostream>

#include <lorina/blif.hpp>
#include <mockturtle/algorithms/equivalence_checking.hpp>
#include <mockturtle/algorithms/miter.hpp>
#include <mockturtle/io/blif_reader.hpp>
#include <mockturtle/networks/klut.hpp>

int main( int argc, char** argv )
{
  using namespace mockturtle;

  if ( argc != 3 )
  {
    std::cerr << "Usage: " << argv[0] << " <gold.blif> <gate.blif>\n";
    return 2;
  }

  klut_network gold;
  klut_network gate;
  if ( lorina::read_blif( argv[1], blif_reader( gold ) ) != lorina::return_code::success )
  {
    std::cerr << "ERROR: failed to read gold BLIF\n";
    return 2;
  }
  if ( lorina::read_blif( argv[2], blif_reader( gate ) ) != lorina::return_code::success )
  {
    std::cerr << "ERROR: failed to read gate BLIF\n";
    return 2;
  }

  const auto combined = miter<klut_network>( gold, gate );
  if ( !combined )
  {
    std::cerr << "ERROR: primary-input or primary-output counts differ\n";
    return 2;
  }

  equivalence_checking_params ps;
  ps.conflict_limit = 0u;
  ps.functional_reduction = true;
  ps.verbose = true;

  equivalence_checking_stats st;
  const auto result = equivalence_checking( *combined, ps, &st );
  if ( !result )
  {
    std::cout << "RESULT=UNDECIDED\n";
    return 3;
  }
  if ( *result )
  {
    std::cout << "RESULT=EQUIVALENT\n";
    return 0;
  }

  std::cout << "RESULT=NOT_EQUIVALENT counterexample_bits="
            << st.counter_example.size() << "\n";
  return 1;
}
