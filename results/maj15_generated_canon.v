// Auto-generated majority circuits (canonical BLIF emission)
// n = 15
// schedule_mode = wallace
// Top modules present (depending on config):
//   - maj_fb_<n>                (folded-bias full scheduler; legacy)
//   - maj_fb_carryonly_<n>      (folded-bias carry-only, stop at w-1)
//   - maj_baseline_strict_<n>   (baseline threshold path)
// You must provide: module fa(input a,b,cin, output sum,cout);

// -----------------------------------------------------------------------------
// Folded-Bias Majority (CSA-only, macro-structured)
// n = 15
// Expect FA primitive: module fa(input a,b,cin, output sum,cout);
// -----------------------------------------------------------------------------

module maj_fb_15 (input  wire [14:0] x, output wire maj);
  // Parameters: th=8, w=3, K=0, schedule=wallace

  // -------- CSA macro schedule --------
  wire raw_s_c0_0, raw_c_c0_0;
  wire raw_s_c0_1, raw_c_c0_1;
  wire raw_s_c0_2, raw_c_c0_2;
  wire raw_s_c0_3, raw_c_c0_3;
  wire raw_s_c0_4, raw_c_c0_4;
  wire w0_s_c0_5, w0_c_c0_5;
  wire w1_s_c0_6, w1_c_c0_6;
  wire w0_s_c1_7, w0_c_c1_7;
  wire w0_s_c1_8, w0_c_c1_8;
  wire w1_s_c1_9, w1_c_c1_9;
  wire w0_s_c2_10, w0_c_c2_10;
  fa u_c0_raw_triple_raw_s_c0_0(.a(x[0]), .b(x[1]), .cin(x[2]), .sum(raw_s_c0_0), .cout(raw_c_c0_0));
  fa u_c0_raw_triple_raw_s_c0_1(.a(x[3]), .b(x[4]), .cin(x[5]), .sum(raw_s_c0_1), .cout(raw_c_c0_1));
  fa u_c0_raw_triple_raw_s_c0_2(.a(x[6]), .b(x[7]), .cin(x[8]), .sum(raw_s_c0_2), .cout(raw_c_c0_2));
  fa u_c0_raw_triple_raw_s_c0_3(.a(x[9]), .b(x[10]), .cin(x[11]), .sum(raw_s_c0_3), .cout(raw_c_c0_3));
  fa u_c0_raw_triple_raw_s_c0_4(.a(x[12]), .b(x[13]), .cin(x[14]), .sum(raw_s_c0_4), .cout(raw_c_c0_4));
  fa u_c0_w0_triple_w0_s_c0_5(.a(raw_s_c0_0), .b(raw_s_c0_1), .cin(raw_s_c0_2), .sum(w0_s_c0_5), .cout(w0_c_c0_5));
  fa u_c0_w1_triple_w1_s_c0_6(.a(w0_s_c0_5), .b(raw_s_c0_3), .cin(raw_s_c0_4), .sum(w1_s_c0_6), .cout(w1_c_c0_6));
  fa u_c1_w0_triple_w0_s_c1_7(.a(raw_c_c0_0), .b(raw_c_c0_1), .cin(raw_c_c0_2), .sum(w0_s_c1_7), .cout(w0_c_c1_7));
  fa u_c1_w0_triple_w0_s_c1_8(.a(raw_c_c0_3), .b(raw_c_c0_4), .cin(w0_c_c0_5), .sum(w0_s_c1_8), .cout(w0_c_c1_8));
  fa u_c1_w1_triple_w1_s_c1_9(.a(w0_s_c1_7), .b(w0_s_c1_8), .cin(w1_c_c0_6), .sum(w1_s_c1_9), .cout(w1_c_c1_9));
  fa u_c2_w0_triple_w0_s_c2_10(.a(w0_c_c1_7), .b(w0_c_c1_8), .cin(w1_c_c1_9), .sum(w0_s_c2_10), .cout(w0_c_c2_10));

  assign maj = w0_c_c2_10;
endmodule

// FA count (folded-bias, CSA-only) for n=15: total=11
// -----------------------------------------------------------------------------
// Baseline STRICT (paper scaffold): CSA (N=2^p-1) → HW + th_N - 1 + Cin
// n = 15
// Expect FA primitive: module fa(input a,b,cin, output sum,cout);
// -----------------------------------------------------------------------------

module maj_baseline_strict_15 (input  wire [14:0] x, output wire maj);
  // Scaffold parameters: p=4, N=2^4-1=15, th_N=8, paired constants=0, schedule=wallace

  // -------- CSA macro schedule on scaffold inputs --------
  wire raw_s_c0_0, raw_c_c0_0;
  wire raw_s_c0_1, raw_c_c0_1;
  wire raw_s_c0_2, raw_c_c0_2;
  wire raw_s_c0_3, raw_c_c0_3;
  wire raw_s_c0_4, raw_c_c0_4;
  wire w0_s_c0_5, w0_c_c0_5;
  wire w1_s_c0_6, w1_c_c0_6;
  wire w0_s_c1_7, w0_c_c1_7;
  wire w0_s_c1_8, w0_c_c1_8;
  wire w1_s_c1_9, w1_c_c1_9;
  wire w0_s_c2_10, w0_c_c2_10;
  fa u_c0_raw_triple_raw_s_c0_0(.a(x[0]), .b(x[1]), .cin(x[2]), .sum(raw_s_c0_0), .cout(raw_c_c0_0));
  fa u_c0_raw_triple_raw_s_c0_1(.a(x[3]), .b(x[4]), .cin(x[5]), .sum(raw_s_c0_1), .cout(raw_c_c0_1));
  fa u_c0_raw_triple_raw_s_c0_2(.a(x[6]), .b(x[7]), .cin(x[8]), .sum(raw_s_c0_2), .cout(raw_c_c0_2));
  fa u_c0_raw_triple_raw_s_c0_3(.a(x[9]), .b(x[10]), .cin(x[11]), .sum(raw_s_c0_3), .cout(raw_c_c0_3));
  fa u_c0_raw_triple_raw_s_c0_4(.a(x[12]), .b(x[13]), .cin(x[14]), .sum(raw_s_c0_4), .cout(raw_c_c0_4));
  fa u_c0_w0_triple_w0_s_c0_5(.a(raw_s_c0_0), .b(raw_s_c0_1), .cin(raw_s_c0_2), .sum(w0_s_c0_5), .cout(w0_c_c0_5));
  fa u_c0_w1_triple_w1_s_c0_6(.a(w0_s_c0_5), .b(raw_s_c0_3), .cin(raw_s_c0_4), .sum(w1_s_c0_6), .cout(w1_c_c0_6));
  fa u_c1_w0_triple_w0_s_c1_7(.a(raw_c_c0_0), .b(raw_c_c0_1), .cin(raw_c_c0_2), .sum(w0_s_c1_7), .cout(w0_c_c1_7));
  fa u_c1_w0_triple_w0_s_c1_8(.a(raw_c_c0_3), .b(raw_c_c0_4), .cin(w0_c_c0_5), .sum(w0_s_c1_8), .cout(w0_c_c1_8));
  fa u_c1_w1_triple_w1_s_c1_9(.a(w0_s_c1_7), .b(w0_s_c1_8), .cin(w1_c_c0_6), .sum(w1_s_c1_9), .cout(w1_c_c1_9));
  fa u_c2_w0_triple_w0_s_c2_10(.a(w0_c_c1_7), .b(w0_c_c1_8), .cin(w1_c_c1_9), .sum(w0_s_c2_10), .cout(w0_c_c2_10));

  // -------- HW bits after CSA (single-rail) --------
  wire hw_0 = w1_s_c0_6;
  wire hw_1 = w1_s_c1_9;
  wire hw_2 = w0_s_c2_10;
  wire hw_3 = w0_c_c2_10;

  // Threshold constant bits (th_N - 1)
  wire T0 = 1'b1;
  wire T1 = 1'b1;
  wire T2 = 1'b1;

  // -------- Full ripple (m bits) for HW + (th_N - 1) + Cin=1 --------
  wire c2_0 = 1'b1; // Cin = 1 (paper comparator)
  wire s2_0, c2_1;
  fa u_th_0(.a(hw_0), .b(T0), .cin(c2_0), .sum(s2_0), .cout(c2_1));
  wire s2_1, c2_2;
  fa u_th_1(.a(hw_1), .b(T1), .cin(c2_1), .sum(s2_1), .cout(c2_2));
  wire s2_2, c2_3;
  fa u_th_2(.a(hw_2), .b(T2), .cin(c2_2), .sum(s2_2), .cout(c2_3));
  wire s2_3, c2_4;
  fa u_th_3(.a(hw_3), .b(1'b0), .cin(c2_3), .sum(s2_3), .cout(c2_4));
  wire c2_m = c2_4;

  assign maj = c2_m;
endmodule

// FA count (baseline STRICT, scaffold) for n=15: CSA=11, CPA(th)=4, total=15