// Auto-generated majority circuits (canonical BLIF emission)
// n = 31
// schedule_mode = dadda
// Top modules present (depending on config):
//   - maj_fb_<n>                (folded-bias full scheduler; legacy)
//   - maj_fb_carryonly_<n>      (folded-bias carry-only, stop at w-1)
//   - maj_baseline_strict_<n>   (baseline threshold path)
// You must provide: module fa(input a,b,cin, output sum,cout);

// -----------------------------------------------------------------------------
// Folded-Bias Majority (CSA-only, macro-structured)
// n = 31
// Expect FA primitive: module fa(input a,b,cin, output sum,cout);
// -----------------------------------------------------------------------------

module maj_fb_31 (input  wire [30:0] x, output wire maj);
  // Parameters: th=16, w=4, K=0, schedule=dadda

  // -------- CSA macro schedule --------
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
  wire d0_s_c0_10, d0_c_c0_10;
  wire d1_s_c0_11, d1_c_c0_11;
  wire d2_s_c0_12, d2_c_c0_12;
  wire d3_s_c0_13, d3_c_c0_13;
  wire d4_s_c0_14, d4_c_c0_14;
  wire d0_s_c1_15, d0_c_c1_15;
  wire d1_s_c1_16, d1_c_c1_16;
  wire d1_s_c1_17, d1_c_c1_17;
  wire d2_s_c1_18, d2_c_c1_18;
  wire d3_s_c1_19, d3_c_c1_19;
  wire d4_s_c1_20, d4_c_c1_20;
  wire d5_s_c1_21, d5_c_c1_21;
  wire d0_s_c2_22, d0_c_c2_22;
  wire d1_s_c2_23, d1_c_c2_23;
  wire d3_s_c2_24, d3_c_c2_24;
  wire d0_s_c3_25, d0_c_c3_25;
  fa u_c0_raw_triple_raw_s_c0_0(.a(x[0]), .b(x[1]), .cin(x[2]), .sum(raw_s_c0_0), .cout(raw_c_c0_0));
  fa u_c0_raw_triple_raw_s_c0_1(.a(x[3]), .b(x[4]), .cin(x[5]), .sum(raw_s_c0_1), .cout(raw_c_c0_1));
  fa u_c0_raw_triple_raw_s_c0_2(.a(x[6]), .b(x[7]), .cin(x[8]), .sum(raw_s_c0_2), .cout(raw_c_c0_2));
  fa u_c0_raw_triple_raw_s_c0_3(.a(x[9]), .b(x[10]), .cin(x[11]), .sum(raw_s_c0_3), .cout(raw_c_c0_3));
  fa u_c0_raw_triple_raw_s_c0_4(.a(x[12]), .b(x[13]), .cin(x[14]), .sum(raw_s_c0_4), .cout(raw_c_c0_4));
  fa u_c0_raw_triple_raw_s_c0_5(.a(x[15]), .b(x[16]), .cin(x[17]), .sum(raw_s_c0_5), .cout(raw_c_c0_5));
  fa u_c0_raw_triple_raw_s_c0_6(.a(x[18]), .b(x[19]), .cin(x[20]), .sum(raw_s_c0_6), .cout(raw_c_c0_6));
  fa u_c0_raw_triple_raw_s_c0_7(.a(x[21]), .b(x[22]), .cin(x[23]), .sum(raw_s_c0_7), .cout(raw_c_c0_7));
  fa u_c0_raw_triple_raw_s_c0_8(.a(x[24]), .b(x[25]), .cin(x[26]), .sum(raw_s_c0_8), .cout(raw_c_c0_8));
  fa u_c0_raw_triple_raw_s_c0_9(.a(x[27]), .b(x[28]), .cin(x[29]), .sum(raw_s_c0_9), .cout(raw_c_c0_9));
  fa u_c0_d0_triple_d0_s_c0_10(.a(raw_s_c0_0), .b(raw_s_c0_1), .cin(raw_s_c0_2), .sum(d0_s_c0_10), .cout(d0_c_c0_10));
  fa u_c0_d1_triple_d1_s_c0_11(.a(d0_s_c0_10), .b(raw_s_c0_3), .cin(raw_s_c0_4), .sum(d1_s_c0_11), .cout(d1_c_c0_11));
  fa u_c0_d2_triple_d2_s_c0_12(.a(d1_s_c0_11), .b(raw_s_c0_5), .cin(raw_s_c0_6), .sum(d2_s_c0_12), .cout(d2_c_c0_12));
  fa u_c0_d3_triple_d3_s_c0_13(.a(d2_s_c0_12), .b(raw_s_c0_7), .cin(raw_s_c0_8), .sum(d3_s_c0_13), .cout(d3_c_c0_13));
  fa u_c0_d4_triple_d4_s_c0_14(.a(d3_s_c0_13), .b(raw_s_c0_9), .cin(x[30]), .sum(d4_s_c0_14), .cout(d4_c_c0_14));
  fa u_c1_d0_triple_d0_s_c1_15(.a(raw_c_c0_0), .b(raw_c_c0_1), .cin(raw_c_c0_2), .sum(d0_s_c1_15), .cout(d0_c_c1_15));
  fa u_c1_d1_triple_d1_s_c1_16(.a(d0_s_c1_15), .b(raw_c_c0_3), .cin(raw_c_c0_4), .sum(d1_s_c1_16), .cout(d1_c_c1_16));
  fa u_c1_d1_triple_d1_s_c1_17(.a(raw_c_c0_5), .b(raw_c_c0_6), .cin(raw_c_c0_7), .sum(d1_s_c1_17), .cout(d1_c_c1_17));
  fa u_c1_d2_triple_d2_s_c1_18(.a(d1_s_c1_16), .b(d1_s_c1_17), .cin(raw_c_c0_8), .sum(d2_s_c1_18), .cout(d2_c_c1_18));
  fa u_c1_d3_triple_d3_s_c1_19(.a(d2_s_c1_18), .b(raw_c_c0_9), .cin(d0_c_c0_10), .sum(d3_s_c1_19), .cout(d3_c_c1_19));
  fa u_c1_d4_triple_d4_s_c1_20(.a(d3_s_c1_19), .b(d1_c_c0_11), .cin(d2_c_c0_12), .sum(d4_s_c1_20), .cout(d4_c_c1_20));
  fa u_c1_d5_triple_d5_s_c1_21(.a(d4_s_c1_20), .b(d3_c_c0_13), .cin(d4_c_c0_14), .sum(d5_s_c1_21), .cout(d5_c_c1_21));
  fa u_c2_d0_triple_d0_s_c2_22(.a(d0_c_c1_15), .b(d1_c_c1_16), .cin(d1_c_c1_17), .sum(d0_s_c2_22), .cout(d0_c_c2_22));
  fa u_c2_d1_triple_d1_s_c2_23(.a(d0_s_c2_22), .b(d2_c_c1_18), .cin(d3_c_c1_19), .sum(d1_s_c2_23), .cout(d1_c_c2_23));
  fa u_c2_d3_triple_d3_s_c2_24(.a(d1_s_c2_23), .b(d4_c_c1_20), .cin(d5_c_c1_21), .sum(d3_s_c2_24), .cout(d3_c_c2_24));
  fa u_c3_d0_triple_d0_s_c3_25(.a(d0_c_c2_22), .b(d1_c_c2_23), .cin(d3_c_c2_24), .sum(d0_s_c3_25), .cout(d0_c_c3_25));

  assign maj = d0_c_c3_25;
endmodule

// FA count (folded-bias, CSA-only) for n=31: total=26
// -----------------------------------------------------------------------------
// Baseline STRICT (paper scaffold): CSA (N=2^p-1) → HW + th_N - 1 + Cin
// n = 31
// Expect FA primitive: module fa(input a,b,cin, output sum,cout);
// -----------------------------------------------------------------------------

module maj_baseline_strict_31 (input  wire [30:0] x, output wire maj);
  // Scaffold parameters: p=5, N=2^5-1=31, th_N=16, paired constants=0, schedule=dadda

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
  wire d0_s_c0_10, d0_c_c0_10;
  wire d1_s_c0_11, d1_c_c0_11;
  wire d2_s_c0_12, d2_c_c0_12;
  wire d3_s_c0_13, d3_c_c0_13;
  wire d4_s_c0_14, d4_c_c0_14;
  wire d0_s_c1_15, d0_c_c1_15;
  wire d1_s_c1_16, d1_c_c1_16;
  wire d1_s_c1_17, d1_c_c1_17;
  wire d2_s_c1_18, d2_c_c1_18;
  wire d3_s_c1_19, d3_c_c1_19;
  wire d4_s_c1_20, d4_c_c1_20;
  wire d5_s_c1_21, d5_c_c1_21;
  wire d0_s_c2_22, d0_c_c2_22;
  wire d1_s_c2_23, d1_c_c2_23;
  wire d3_s_c2_24, d3_c_c2_24;
  wire d0_s_c3_25, d0_c_c3_25;
  fa u_c0_raw_triple_raw_s_c0_0(.a(x[0]), .b(x[1]), .cin(x[2]), .sum(raw_s_c0_0), .cout(raw_c_c0_0));
  fa u_c0_raw_triple_raw_s_c0_1(.a(x[3]), .b(x[4]), .cin(x[5]), .sum(raw_s_c0_1), .cout(raw_c_c0_1));
  fa u_c0_raw_triple_raw_s_c0_2(.a(x[6]), .b(x[7]), .cin(x[8]), .sum(raw_s_c0_2), .cout(raw_c_c0_2));
  fa u_c0_raw_triple_raw_s_c0_3(.a(x[9]), .b(x[10]), .cin(x[11]), .sum(raw_s_c0_3), .cout(raw_c_c0_3));
  fa u_c0_raw_triple_raw_s_c0_4(.a(x[12]), .b(x[13]), .cin(x[14]), .sum(raw_s_c0_4), .cout(raw_c_c0_4));
  fa u_c0_raw_triple_raw_s_c0_5(.a(x[15]), .b(x[16]), .cin(x[17]), .sum(raw_s_c0_5), .cout(raw_c_c0_5));
  fa u_c0_raw_triple_raw_s_c0_6(.a(x[18]), .b(x[19]), .cin(x[20]), .sum(raw_s_c0_6), .cout(raw_c_c0_6));
  fa u_c0_raw_triple_raw_s_c0_7(.a(x[21]), .b(x[22]), .cin(x[23]), .sum(raw_s_c0_7), .cout(raw_c_c0_7));
  fa u_c0_raw_triple_raw_s_c0_8(.a(x[24]), .b(x[25]), .cin(x[26]), .sum(raw_s_c0_8), .cout(raw_c_c0_8));
  fa u_c0_raw_triple_raw_s_c0_9(.a(x[27]), .b(x[28]), .cin(x[29]), .sum(raw_s_c0_9), .cout(raw_c_c0_9));
  fa u_c0_d0_triple_d0_s_c0_10(.a(raw_s_c0_0), .b(raw_s_c0_1), .cin(raw_s_c0_2), .sum(d0_s_c0_10), .cout(d0_c_c0_10));
  fa u_c0_d1_triple_d1_s_c0_11(.a(d0_s_c0_10), .b(raw_s_c0_3), .cin(raw_s_c0_4), .sum(d1_s_c0_11), .cout(d1_c_c0_11));
  fa u_c0_d2_triple_d2_s_c0_12(.a(d1_s_c0_11), .b(raw_s_c0_5), .cin(raw_s_c0_6), .sum(d2_s_c0_12), .cout(d2_c_c0_12));
  fa u_c0_d3_triple_d3_s_c0_13(.a(d2_s_c0_12), .b(raw_s_c0_7), .cin(raw_s_c0_8), .sum(d3_s_c0_13), .cout(d3_c_c0_13));
  fa u_c0_d4_triple_d4_s_c0_14(.a(d3_s_c0_13), .b(raw_s_c0_9), .cin(x[30]), .sum(d4_s_c0_14), .cout(d4_c_c0_14));
  fa u_c1_d0_triple_d0_s_c1_15(.a(raw_c_c0_0), .b(raw_c_c0_1), .cin(raw_c_c0_2), .sum(d0_s_c1_15), .cout(d0_c_c1_15));
  fa u_c1_d1_triple_d1_s_c1_16(.a(d0_s_c1_15), .b(raw_c_c0_3), .cin(raw_c_c0_4), .sum(d1_s_c1_16), .cout(d1_c_c1_16));
  fa u_c1_d1_triple_d1_s_c1_17(.a(raw_c_c0_5), .b(raw_c_c0_6), .cin(raw_c_c0_7), .sum(d1_s_c1_17), .cout(d1_c_c1_17));
  fa u_c1_d2_triple_d2_s_c1_18(.a(d1_s_c1_16), .b(d1_s_c1_17), .cin(raw_c_c0_8), .sum(d2_s_c1_18), .cout(d2_c_c1_18));
  fa u_c1_d3_triple_d3_s_c1_19(.a(d2_s_c1_18), .b(raw_c_c0_9), .cin(d0_c_c0_10), .sum(d3_s_c1_19), .cout(d3_c_c1_19));
  fa u_c1_d4_triple_d4_s_c1_20(.a(d3_s_c1_19), .b(d1_c_c0_11), .cin(d2_c_c0_12), .sum(d4_s_c1_20), .cout(d4_c_c1_20));
  fa u_c1_d5_triple_d5_s_c1_21(.a(d4_s_c1_20), .b(d3_c_c0_13), .cin(d4_c_c0_14), .sum(d5_s_c1_21), .cout(d5_c_c1_21));
  fa u_c2_d0_triple_d0_s_c2_22(.a(d0_c_c1_15), .b(d1_c_c1_16), .cin(d1_c_c1_17), .sum(d0_s_c2_22), .cout(d0_c_c2_22));
  fa u_c2_d1_triple_d1_s_c2_23(.a(d0_s_c2_22), .b(d2_c_c1_18), .cin(d3_c_c1_19), .sum(d1_s_c2_23), .cout(d1_c_c2_23));
  fa u_c2_d3_triple_d3_s_c2_24(.a(d1_s_c2_23), .b(d4_c_c1_20), .cin(d5_c_c1_21), .sum(d3_s_c2_24), .cout(d3_c_c2_24));
  fa u_c3_d0_triple_d0_s_c3_25(.a(d0_c_c2_22), .b(d1_c_c2_23), .cin(d3_c_c2_24), .sum(d0_s_c3_25), .cout(d0_c_c3_25));

  // -------- HW bits after CSA (single-rail) --------
  wire hw_0 = d4_s_c0_14;
  wire hw_1 = d5_s_c1_21;
  wire hw_2 = d3_s_c2_24;
  wire hw_3 = d0_s_c3_25;
  wire hw_4 = d0_c_c3_25;

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

// FA count (baseline STRICT, scaffold) for n=31: CSA=26, CPA(th)=5, total=31