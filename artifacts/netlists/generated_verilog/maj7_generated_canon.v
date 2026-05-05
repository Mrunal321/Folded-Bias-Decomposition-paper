// Auto-generated majority circuits (canonical BLIF emission)
// n = 7
// schedule_mode = dadda
// Top modules present (depending on config):
//   - maj_fb_<n>                (folded-bias full scheduler; legacy)
//   - maj_fb_carryonly_<n>      (folded-bias carry-only, stop at w-1)
//   - maj_baseline_strict_<n>   (baseline threshold path)
// You must provide: module fa(input a,b,cin, output sum,cout);

// -----------------------------------------------------------------------------
// Folded-Bias Majority (CSA-only, macro-structured)
// n = 7
// Expect FA primitive: module fa(input a,b,cin, output sum,cout);
// -----------------------------------------------------------------------------

module maj_fb_7 (input  wire [6:0] x, output wire maj);
  // Parameters: th=4, w=2, K=0, schedule=dadda

  // -------- CSA macro schedule --------
  wire raw_s_c0_0, raw_c_c0_0;
  wire raw_s_c0_1, raw_c_c0_1;
  wire d0_s_c0_2, d0_c_c0_2;
  wire d0_s_c1_3, d0_c_c1_3;
  fa u_c0_raw_triple_raw_s_c0_0(.a(x[0]), .b(x[1]), .cin(x[2]), .sum(raw_s_c0_0), .cout(raw_c_c0_0));
  fa u_c0_raw_triple_raw_s_c0_1(.a(x[3]), .b(x[4]), .cin(x[5]), .sum(raw_s_c0_1), .cout(raw_c_c0_1));
  fa u_c0_d0_triple_d0_s_c0_2(.a(raw_s_c0_0), .b(raw_s_c0_1), .cin(x[6]), .sum(d0_s_c0_2), .cout(d0_c_c0_2));
  fa u_c1_d0_triple_d0_s_c1_3(.a(raw_c_c0_0), .b(raw_c_c0_1), .cin(d0_c_c0_2), .sum(d0_s_c1_3), .cout(d0_c_c1_3));

  assign maj = d0_c_c1_3;
endmodule

// FA count (folded-bias, CSA-only) for n=7: total=4
// -----------------------------------------------------------------------------
// Baseline STRICT (paper scaffold): CSA (N=2^p-1) → HW + th_N - 1 + Cin
// n = 7
// Expect FA primitive: module fa(input a,b,cin, output sum,cout);
// -----------------------------------------------------------------------------

module maj_baseline_strict_7 (input  wire [6:0] x, output wire maj);
  // Scaffold parameters: p=3, N=2^3-1=7, th_N=4, paired constants=0, schedule=dadda

  // -------- CSA macro schedule on scaffold inputs --------
  wire raw_s_c0_0, raw_c_c0_0;
  wire raw_s_c0_1, raw_c_c0_1;
  wire d0_s_c0_2, d0_c_c0_2;
  wire d0_s_c1_3, d0_c_c1_3;
  fa u_c0_raw_triple_raw_s_c0_0(.a(x[0]), .b(x[1]), .cin(x[2]), .sum(raw_s_c0_0), .cout(raw_c_c0_0));
  fa u_c0_raw_triple_raw_s_c0_1(.a(x[3]), .b(x[4]), .cin(x[5]), .sum(raw_s_c0_1), .cout(raw_c_c0_1));
  fa u_c0_d0_triple_d0_s_c0_2(.a(raw_s_c0_0), .b(raw_s_c0_1), .cin(x[6]), .sum(d0_s_c0_2), .cout(d0_c_c0_2));
  fa u_c1_d0_triple_d0_s_c1_3(.a(raw_c_c0_0), .b(raw_c_c0_1), .cin(d0_c_c0_2), .sum(d0_s_c1_3), .cout(d0_c_c1_3));

  // -------- HW bits after CSA (single-rail) --------
  wire hw_0 = d0_s_c0_2;
  wire hw_1 = d0_s_c1_3;
  wire hw_2 = d0_c_c1_3;

  // Threshold constant bits (th_N - 1)
  wire T0 = 1'b1;
  wire T1 = 1'b1;

  // -------- Full ripple (m bits) for HW + (th_N - 1) + Cin=1 --------
  wire c2_0 = 1'b1; // Cin = 1 (paper comparator)
  wire s2_0, c2_1;
  fa u_th_0(.a(hw_0), .b(T0), .cin(c2_0), .sum(s2_0), .cout(c2_1));
  wire s2_1, c2_2;
  fa u_th_1(.a(hw_1), .b(T1), .cin(c2_1), .sum(s2_1), .cout(c2_2));
  wire s2_2, c2_3;
  fa u_th_2(.a(hw_2), .b(1'b0), .cin(c2_2), .sum(s2_2), .cout(c2_3));
  wire c2_m = c2_3;

  assign maj = c2_m;
endmodule

// FA count (baseline STRICT, scaffold) for n=7: CSA=4, CPA(th)=3, total=7