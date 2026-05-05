// Auto-generated majority circuits (canonical BLIF emission)
// n = 19
// schedule_mode = wallace
// Top modules present (depending on config):
//   - maj_fb_<n>                (folded-bias full scheduler; legacy)
//   - maj_fb_carryonly_<n>      (folded-bias carry-only, stop at w-1)
//   - maj_baseline_strict_<n>   (baseline threshold path)
// You must provide: module fa(input a,b,cin, output sum,cout);

// -----------------------------------------------------------------------------
// Folded-Bias Majority (CSA-only, macro-structured)
// n = 19
// Expect FA primitive: module fa(input a,b,cin, output sum,cout);
// -----------------------------------------------------------------------------

module maj_fb_19 (input  wire [18:0] x, output wire maj);
  // Parameters: th=10, w=4, K=6, schedule=wallace
  wire K1 = 1'b1;
  wire K2 = 1'b1;

  // -------- CSA macro schedule --------
  wire raw_s_c0_0, raw_c_c0_0;
  wire raw_s_c0_1, raw_c_c0_1;
  wire raw_s_c0_2, raw_c_c0_2;
  wire raw_s_c0_3, raw_c_c0_3;
  wire raw_s_c0_4, raw_c_c0_4;
  wire raw_s_c0_5, raw_c_c0_5;
  wire w0_s_c0_6, w0_c_c0_6;
  wire w0_s_c0_7, w0_c_c0_7;
  wire w1_s_c0_8, w1_c_c0_8;
  wire w0_s_c1_9, w0_c_c1_9;
  wire w0_s_c1_10, w0_c_c1_10;
  wire w0_s_c1_11, w0_c_c1_11;
  wire w1_s_c1_12, w1_c_c1_12;
  wire w2_p_s_c1_13, w2_p_c_c1_13;
  wire w0_s_c2_14, w0_c_c2_14;
  wire w0_s_c2_15, w0_c_c2_15;
  wire w1_p_s_c2_16, w1_p_c_c2_16;
  wire w0_s_c3_17, w0_c_c3_17;
  fa u_c0_raw_triple_raw_s_c0_0(.a(x[0]), .b(x[1]), .cin(x[2]), .sum(raw_s_c0_0), .cout(raw_c_c0_0));
  fa u_c0_raw_triple_raw_s_c0_1(.a(x[3]), .b(x[4]), .cin(x[5]), .sum(raw_s_c0_1), .cout(raw_c_c0_1));
  fa u_c0_raw_triple_raw_s_c0_2(.a(x[6]), .b(x[7]), .cin(x[8]), .sum(raw_s_c0_2), .cout(raw_c_c0_2));
  fa u_c0_raw_triple_raw_s_c0_3(.a(x[9]), .b(x[10]), .cin(x[11]), .sum(raw_s_c0_3), .cout(raw_c_c0_3));
  fa u_c0_raw_triple_raw_s_c0_4(.a(x[12]), .b(x[13]), .cin(x[14]), .sum(raw_s_c0_4), .cout(raw_c_c0_4));
  fa u_c0_raw_triple_raw_s_c0_5(.a(x[15]), .b(x[16]), .cin(x[17]), .sum(raw_s_c0_5), .cout(raw_c_c0_5));
  fa u_c0_w0_triple_w0_s_c0_6(.a(raw_s_c0_0), .b(raw_s_c0_1), .cin(raw_s_c0_2), .sum(w0_s_c0_6), .cout(w0_c_c0_6));
  fa u_c0_w0_triple_w0_s_c0_7(.a(raw_s_c0_3), .b(raw_s_c0_4), .cin(raw_s_c0_5), .sum(w0_s_c0_7), .cout(w0_c_c0_7));
  fa u_c0_w1_triple_w1_s_c0_8(.a(w0_s_c0_6), .b(w0_s_c0_7), .cin(x[18]), .sum(w1_s_c0_8), .cout(w1_c_c0_8));
  fa u_c1_w0_triple_w0_s_c1_9(.a(raw_c_c0_0), .b(raw_c_c0_1), .cin(raw_c_c0_2), .sum(w0_s_c1_9), .cout(w0_c_c1_9));
  fa u_c1_w0_triple_w0_s_c1_10(.a(raw_c_c0_3), .b(raw_c_c0_4), .cin(raw_c_c0_5), .sum(w0_s_c1_10), .cout(w0_c_c1_10));
  fa u_c1_w0_triple_w0_s_c1_11(.a(w0_c_c0_6), .b(w0_c_c0_7), .cin(w1_c_c0_8), .sum(w0_s_c1_11), .cout(w0_c_c1_11));
  fa u_c1_w1_triple_w1_s_c1_12(.a(w0_s_c1_9), .b(w0_s_c1_10), .cin(w0_s_c1_11), .sum(w1_s_c1_12), .cout(w1_c_c1_12));
  fa u_c1_w2_pair_w2_p_s_c1_13(.a(w1_s_c1_12), .b(K1), .cin(1'b0), .sum(w2_p_s_c1_13), .cout(w2_p_c_c1_13));
  fa u_c2_w0_triple_w0_s_c2_14(.a(w0_c_c1_9), .b(w0_c_c1_10), .cin(w0_c_c1_11), .sum(w0_s_c2_14), .cout(w0_c_c2_14));
  fa u_c2_w0_triple_w0_s_c2_15(.a(w1_c_c1_12), .b(w2_p_c_c1_13), .cin(K2), .sum(w0_s_c2_15), .cout(w0_c_c2_15));
  fa u_c2_w1_pair_w1_p_s_c2_16(.a(w0_s_c2_14), .b(w0_s_c2_15), .cin(1'b0), .sum(w1_p_s_c2_16), .cout(w1_p_c_c2_16));
  fa u_c3_w0_triple_w0_s_c3_17(.a(w0_c_c2_14), .b(w0_c_c2_15), .cin(w1_p_c_c2_16), .sum(w0_s_c3_17), .cout(w0_c_c3_17));

  assign maj = w0_c_c3_17;
endmodule

// FA count (folded-bias, CSA-only) for n=19: total=18
// -----------------------------------------------------------------------------
// Baseline STRICT (paper scaffold): CSA (N=2^p-1) → HW + th_N - 1 + Cin
// n = 19
// Expect FA primitive: module fa(input a,b,cin, output sum,cout);
// -----------------------------------------------------------------------------

module maj_baseline_strict_19 (input  wire [18:0] x, output wire maj);
  // Scaffold parameters: p=5, N=2^5-1=31, th_N=16, paired constants=6, schedule=wallace

  // -------- CSA macro schedule on scaffold inputs --------
  wire raw_s_c0_0, raw_c_c0_0;
  wire raw_s_c0_1, raw_c_c0_1;
  wire raw_s_c0_2, raw_c_c0_2;
  wire raw_s_c0_3, raw_c_c0_3;
  wire raw_s_c0_4, raw_c_c0_4;
  wire raw_s_c0_5, raw_c_c0_5;
  wire raw_s_c0_6, raw_c_c0_6;
  wire raw_s_c0_7, raw_c_c0_7;
  wire raw_s_c0_8, raw_c_c0_8;
  wire raw_s_c0_9, raw_c_c0_9;
  wire w0_s_c0_10, w0_c_c0_10;
  wire w0_s_c0_11, w0_c_c0_11;
  wire w0_s_c0_12, w0_c_c0_12;
  wire w1_s_c0_13, w1_c_c0_13;
  wire w2_s_c0_14, w2_c_c0_14;
  wire w0_s_c1_15, w0_c_c1_15;
  wire w0_s_c1_16, w0_c_c1_16;
  wire w0_s_c1_17, w0_c_c1_17;
  wire w0_s_c1_18, w0_c_c1_18;
  wire w0_s_c1_19, w0_c_c1_19;
  wire w1_s_c1_20, w1_c_c1_20;
  wire w2_s_c1_21, w2_c_c1_21;
  wire w0_s_c2_22, w0_c_c2_22;
  wire w0_s_c2_23, w0_c_c2_23;
  wire w1_s_c2_24, w1_c_c2_24;
  wire w0_s_c3_25, w0_c_c3_25;
  fa u_c0_raw_triple_raw_s_c0_0(.a(x[0]), .b(x[1]), .cin(x[2]), .sum(raw_s_c0_0), .cout(raw_c_c0_0));
  fa u_c0_raw_triple_raw_s_c0_1(.a(x[3]), .b(x[4]), .cin(x[5]), .sum(raw_s_c0_1), .cout(raw_c_c0_1));
  fa u_c0_raw_triple_raw_s_c0_2(.a(x[6]), .b(x[7]), .cin(x[8]), .sum(raw_s_c0_2), .cout(raw_c_c0_2));
  fa u_c0_raw_triple_raw_s_c0_3(.a(x[9]), .b(x[10]), .cin(x[11]), .sum(raw_s_c0_3), .cout(raw_c_c0_3));
  fa u_c0_raw_triple_raw_s_c0_4(.a(x[12]), .b(x[13]), .cin(x[14]), .sum(raw_s_c0_4), .cout(raw_c_c0_4));
  fa u_c0_raw_triple_raw_s_c0_5(.a(x[15]), .b(x[16]), .cin(x[17]), .sum(raw_s_c0_5), .cout(raw_c_c0_5));
  fa u_c0_raw_triple_raw_s_c0_6(.a(x[18]), .b(1'b1), .cin(1'b1), .sum(raw_s_c0_6), .cout(raw_c_c0_6));
  fa u_c0_raw_triple_raw_s_c0_7(.a(1'b1), .b(1'b1), .cin(1'b1), .sum(raw_s_c0_7), .cout(raw_c_c0_7));
  fa u_c0_raw_triple_raw_s_c0_8(.a(1'b1), .b(1'b0), .cin(1'b0), .sum(raw_s_c0_8), .cout(raw_c_c0_8));
  fa u_c0_raw_triple_raw_s_c0_9(.a(1'b0), .b(1'b0), .cin(1'b0), .sum(raw_s_c0_9), .cout(raw_c_c0_9));
  fa u_c0_w0_triple_w0_s_c0_10(.a(raw_s_c0_0), .b(raw_s_c0_1), .cin(raw_s_c0_2), .sum(w0_s_c0_10), .cout(w0_c_c0_10));
  fa u_c0_w0_triple_w0_s_c0_11(.a(raw_s_c0_3), .b(raw_s_c0_4), .cin(raw_s_c0_5), .sum(w0_s_c0_11), .cout(w0_c_c0_11));
  fa u_c0_w0_triple_w0_s_c0_12(.a(raw_s_c0_6), .b(raw_s_c0_7), .cin(raw_s_c0_8), .sum(w0_s_c0_12), .cout(w0_c_c0_12));
  fa u_c0_w1_triple_w1_s_c0_13(.a(w0_s_c0_10), .b(w0_s_c0_11), .cin(w0_s_c0_12), .sum(w1_s_c0_13), .cout(w1_c_c0_13));
  fa u_c0_w2_triple_w2_s_c0_14(.a(w1_s_c0_13), .b(raw_s_c0_9), .cin(1'b0), .sum(w2_s_c0_14), .cout(w2_c_c0_14));
  fa u_c1_w0_triple_w0_s_c1_15(.a(raw_c_c0_0), .b(raw_c_c0_1), .cin(raw_c_c0_2), .sum(w0_s_c1_15), .cout(w0_c_c1_15));
  fa u_c1_w0_triple_w0_s_c1_16(.a(raw_c_c0_3), .b(raw_c_c0_4), .cin(raw_c_c0_5), .sum(w0_s_c1_16), .cout(w0_c_c1_16));
  fa u_c1_w0_triple_w0_s_c1_17(.a(raw_c_c0_6), .b(raw_c_c0_7), .cin(raw_c_c0_8), .sum(w0_s_c1_17), .cout(w0_c_c1_17));
  fa u_c1_w0_triple_w0_s_c1_18(.a(raw_c_c0_9), .b(w0_c_c0_10), .cin(w0_c_c0_11), .sum(w0_s_c1_18), .cout(w0_c_c1_18));
  fa u_c1_w0_triple_w0_s_c1_19(.a(w0_c_c0_12), .b(w1_c_c0_13), .cin(w2_c_c0_14), .sum(w0_s_c1_19), .cout(w0_c_c1_19));
  fa u_c1_w1_triple_w1_s_c1_20(.a(w0_s_c1_15), .b(w0_s_c1_16), .cin(w0_s_c1_17), .sum(w1_s_c1_20), .cout(w1_c_c1_20));
  fa u_c1_w2_triple_w2_s_c1_21(.a(w1_s_c1_20), .b(w0_s_c1_18), .cin(w0_s_c1_19), .sum(w2_s_c1_21), .cout(w2_c_c1_21));
  fa u_c2_w0_triple_w0_s_c2_22(.a(w0_c_c1_15), .b(w0_c_c1_16), .cin(w0_c_c1_17), .sum(w0_s_c2_22), .cout(w0_c_c2_22));
  fa u_c2_w0_triple_w0_s_c2_23(.a(w0_c_c1_18), .b(w0_c_c1_19), .cin(w1_c_c1_20), .sum(w0_s_c2_23), .cout(w0_c_c2_23));
  fa u_c2_w1_triple_w1_s_c2_24(.a(w0_s_c2_22), .b(w0_s_c2_23), .cin(w2_c_c1_21), .sum(w1_s_c2_24), .cout(w1_c_c2_24));
  fa u_c3_w0_triple_w0_s_c3_25(.a(w0_c_c2_22), .b(w0_c_c2_23), .cin(w1_c_c2_24), .sum(w0_s_c3_25), .cout(w0_c_c3_25));

  // -------- HW bits after CSA (single-rail) --------
  wire hw_0 = w2_s_c0_14;
  wire hw_1 = w2_s_c1_21;
  wire hw_2 = w1_s_c2_24;
  wire hw_3 = w0_s_c3_25;
  wire hw_4 = w0_c_c3_25;

  // Threshold constant bits (th_N - 1)
  wire T0 = 1'b1;
  wire T1 = 1'b1;
  wire T2 = 1'b1;
  wire T3 = 1'b1;

  // -------- Full ripple (m bits) for HW + (th_N - 1) + Cin=1 --------
  wire c2_0 = 1'b1; // Cin = 1 (paper comparator)
  wire s2_0, c2_1;
  fa u_th_0(.a(hw_0), .b(T0), .cin(c2_0), .sum(s2_0), .cout(c2_1));
  wire s2_1, c2_2;
  fa u_th_1(.a(hw_1), .b(T1), .cin(c2_1), .sum(s2_1), .cout(c2_2));
  wire s2_2, c2_3;
  fa u_th_2(.a(hw_2), .b(T2), .cin(c2_2), .sum(s2_2), .cout(c2_3));
  wire s2_3, c2_4;
  fa u_th_3(.a(hw_3), .b(T3), .cin(c2_3), .sum(s2_3), .cout(c2_4));
  wire s2_4, c2_5;
  fa u_th_4(.a(hw_4), .b(1'b0), .cin(c2_4), .sum(s2_4), .cout(c2_5));
  wire c2_m = c2_5;

  assign maj = c2_m;
endmodule

// FA count (baseline STRICT, scaffold) for n=19: CSA=26, CPA(th)=5, total=31