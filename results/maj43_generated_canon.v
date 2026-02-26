// Auto-generated majority circuits (canonical BLIF emission)
// n = 43
// schedule_mode = dadda
// Top modules present (depending on config):
//   - maj_fb_<n>                (folded-bias full scheduler; legacy)
//   - maj_fb_carryonly_<n>      (folded-bias carry-only, stop at w-1)
//   - maj_baseline_strict_<n>   (baseline threshold path)
// You must provide: module fa(input a,b,cin, output sum,cout);

// -----------------------------------------------------------------------------
// Folded-Bias Majority (CSA-only, macro-structured)
// n = 43
// Expect FA primitive: module fa(input a,b,cin, output sum,cout);
// -----------------------------------------------------------------------------

module maj_fb_43 (input  wire [42:0] x, output wire maj);
  // Parameters: th=22, w=5, K=10, schedule=dadda
  wire K1 = 1'b1;
  wire K3 = 1'b1;

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
  wire raw_s_c0_10, raw_c_c0_10;
  wire raw_s_c0_11, raw_c_c0_11;
  wire raw_s_c0_12, raw_c_c0_12;
  wire raw_s_c0_13, raw_c_c0_13;
  wire d0_s_c0_14, d0_c_c0_14;
  wire d1_s_c0_15, d1_c_c0_15;
  wire d1_s_c0_16, d1_c_c0_16;
  wire d2_s_c0_17, d2_c_c0_17;
  wire d3_s_c0_18, d3_c_c0_18;
  wire d4_s_c0_19, d4_c_c0_19;
  wire d5_s_c0_20, d5_c_c0_20;
  wire d0_s_c1_21, d0_c_c1_21;
  wire d1_s_c1_22, d1_c_c1_22;
  wire d1_s_c1_23, d1_c_c1_23;
  wire d1_s_c1_24, d1_c_c1_24;
  wire d2_s_c1_25, d2_c_c1_25;
  wire d2_s_c1_26, d2_c_c1_26;
  wire d3_s_c1_27, d3_c_c1_27;
  wire d3_s_c1_28, d3_c_c1_28;
  wire d4_s_c1_29, d4_c_c1_29;
  wire d5_s_c1_30, d5_c_c1_30;
  wire d7_p_s_c1_31, d7_p_c_c1_31;
  wire d0_s_c2_32, d0_c_c2_32;
  wire d1_s_c2_33, d1_c_c2_33;
  wire d2_s_c2_34, d2_c_c2_34;
  wire d3_s_c2_35, d3_c_c2_35;
  wire d4_s_c2_36, d4_c_c2_36;
  wire d0_s_c3_37, d0_c_c3_37;
  wire d1_s_c3_38, d1_c_c3_38;
  wire d3_p_s_c3_39, d3_p_c_c3_39;
  wire d0_s_c4_40, d0_c_c4_40;
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
  fa u_c0_raw_triple_raw_s_c0_10(.a(x[30]), .b(x[31]), .cin(x[32]), .sum(raw_s_c0_10), .cout(raw_c_c0_10));
  fa u_c0_raw_triple_raw_s_c0_11(.a(x[33]), .b(x[34]), .cin(x[35]), .sum(raw_s_c0_11), .cout(raw_c_c0_11));
  fa u_c0_raw_triple_raw_s_c0_12(.a(x[36]), .b(x[37]), .cin(x[38]), .sum(raw_s_c0_12), .cout(raw_c_c0_12));
  fa u_c0_raw_triple_raw_s_c0_13(.a(x[39]), .b(x[40]), .cin(x[41]), .sum(raw_s_c0_13), .cout(raw_c_c0_13));
  fa u_c0_d0_triple_d0_s_c0_14(.a(raw_s_c0_0), .b(raw_s_c0_1), .cin(raw_s_c0_2), .sum(d0_s_c0_14), .cout(d0_c_c0_14));
  fa u_c0_d1_triple_d1_s_c0_15(.a(d0_s_c0_14), .b(raw_s_c0_3), .cin(raw_s_c0_4), .sum(d1_s_c0_15), .cout(d1_c_c0_15));
  fa u_c0_d1_triple_d1_s_c0_16(.a(raw_s_c0_5), .b(raw_s_c0_6), .cin(raw_s_c0_7), .sum(d1_s_c0_16), .cout(d1_c_c0_16));
  fa u_c0_d2_triple_d2_s_c0_17(.a(d1_s_c0_15), .b(d1_s_c0_16), .cin(raw_s_c0_8), .sum(d2_s_c0_17), .cout(d2_c_c0_17));
  fa u_c0_d3_triple_d3_s_c0_18(.a(d2_s_c0_17), .b(raw_s_c0_9), .cin(raw_s_c0_10), .sum(d3_s_c0_18), .cout(d3_c_c0_18));
  fa u_c0_d4_triple_d4_s_c0_19(.a(d3_s_c0_18), .b(raw_s_c0_11), .cin(raw_s_c0_12), .sum(d4_s_c0_19), .cout(d4_c_c0_19));
  fa u_c0_d5_triple_d5_s_c0_20(.a(d4_s_c0_19), .b(raw_s_c0_13), .cin(x[42]), .sum(d5_s_c0_20), .cout(d5_c_c0_20));
  fa u_c1_d0_triple_d0_s_c1_21(.a(raw_c_c0_0), .b(raw_c_c0_1), .cin(raw_c_c0_2), .sum(d0_s_c1_21), .cout(d0_c_c1_21));
  fa u_c1_d1_triple_d1_s_c1_22(.a(d0_s_c1_21), .b(raw_c_c0_3), .cin(raw_c_c0_4), .sum(d1_s_c1_22), .cout(d1_c_c1_22));
  fa u_c1_d1_triple_d1_s_c1_23(.a(raw_c_c0_5), .b(raw_c_c0_6), .cin(raw_c_c0_7), .sum(d1_s_c1_23), .cout(d1_c_c1_23));
  fa u_c1_d1_triple_d1_s_c1_24(.a(raw_c_c0_8), .b(raw_c_c0_9), .cin(raw_c_c0_10), .sum(d1_s_c1_24), .cout(d1_c_c1_24));
  fa u_c1_d2_triple_d2_s_c1_25(.a(d1_s_c1_22), .b(d1_s_c1_23), .cin(d1_s_c1_24), .sum(d2_s_c1_25), .cout(d2_c_c1_25));
  fa u_c1_d2_triple_d2_s_c1_26(.a(raw_c_c0_11), .b(raw_c_c0_12), .cin(raw_c_c0_13), .sum(d2_s_c1_26), .cout(d2_c_c1_26));
  fa u_c1_d3_triple_d3_s_c1_27(.a(d2_s_c1_25), .b(d2_s_c1_26), .cin(d0_c_c0_14), .sum(d3_s_c1_27), .cout(d3_c_c1_27));
  fa u_c1_d3_triple_d3_s_c1_28(.a(d1_c_c0_15), .b(d1_c_c0_16), .cin(d2_c_c0_17), .sum(d3_s_c1_28), .cout(d3_c_c1_28));
  fa u_c1_d4_triple_d4_s_c1_29(.a(d3_s_c1_27), .b(d3_s_c1_28), .cin(d3_c_c0_18), .sum(d4_s_c1_29), .cout(d4_c_c1_29));
  fa u_c1_d5_triple_d5_s_c1_30(.a(d4_s_c1_29), .b(d4_c_c0_19), .cin(d5_c_c0_20), .sum(d5_s_c1_30), .cout(d5_c_c1_30));
  fa u_c1_d7_pair_d7_p_s_c1_31(.a(d5_s_c1_30), .b(K1), .cin(1'b0), .sum(d7_p_s_c1_31), .cout(d7_p_c_c1_31));
  fa u_c2_d0_triple_d0_s_c2_32(.a(d0_c_c1_21), .b(d1_c_c1_22), .cin(d1_c_c1_23), .sum(d0_s_c2_32), .cout(d0_c_c2_32));
  fa u_c2_d1_triple_d1_s_c2_33(.a(d0_s_c2_32), .b(d1_c_c1_24), .cin(d2_c_c1_25), .sum(d1_s_c2_33), .cout(d1_c_c2_33));
  fa u_c2_d2_triple_d2_s_c2_34(.a(d1_s_c2_33), .b(d2_c_c1_26), .cin(d3_c_c1_27), .sum(d2_s_c2_34), .cout(d2_c_c2_34));
  fa u_c2_d3_triple_d3_s_c2_35(.a(d2_s_c2_34), .b(d3_c_c1_28), .cin(d4_c_c1_29), .sum(d3_s_c2_35), .cout(d3_c_c2_35));
  fa u_c2_d4_triple_d4_s_c2_36(.a(d3_s_c2_35), .b(d5_c_c1_30), .cin(d7_p_c_c1_31), .sum(d4_s_c2_36), .cout(d4_c_c2_36));
  fa u_c3_d0_triple_d0_s_c3_37(.a(d0_c_c2_32), .b(d1_c_c2_33), .cin(d2_c_c2_34), .sum(d0_s_c3_37), .cout(d0_c_c3_37));
  fa u_c3_d1_triple_d1_s_c3_38(.a(d0_s_c3_37), .b(d3_c_c2_35), .cin(d4_c_c2_36), .sum(d1_s_c3_38), .cout(d1_c_c3_38));
  fa u_c3_d3_pair_d3_p_s_c3_39(.a(d1_s_c3_38), .b(K3), .cin(1'b0), .sum(d3_p_s_c3_39), .cout(d3_p_c_c3_39));
  fa u_c4_d0_triple_d0_s_c4_40(.a(d0_c_c3_37), .b(d1_c_c3_38), .cin(d3_p_c_c3_39), .sum(d0_s_c4_40), .cout(d0_c_c4_40));

  assign maj = d0_c_c4_40;
endmodule

// FA count (folded-bias, CSA-only) for n=43: total=41
// -----------------------------------------------------------------------------
// Baseline STRICT (paper scaffold): CSA (N=2^p-1) → HW + th_N - 1 + Cin
// n = 43
// Expect FA primitive: module fa(input a,b,cin, output sum,cout);
// -----------------------------------------------------------------------------

module maj_baseline_strict_43 (input  wire [42:0] x, output wire maj);
  // Scaffold parameters: p=6, N=2^6-1=63, th_N=32, paired constants=10, schedule=dadda

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
  wire raw_s_c0_10, raw_c_c0_10;
  wire raw_s_c0_11, raw_c_c0_11;
  wire raw_s_c0_12, raw_c_c0_12;
  wire raw_s_c0_13, raw_c_c0_13;
  wire raw_s_c0_14, raw_c_c0_14;
  wire raw_s_c0_15, raw_c_c0_15;
  wire raw_s_c0_16, raw_c_c0_16;
  wire raw_s_c0_17, raw_c_c0_17;
  wire raw_s_c0_18, raw_c_c0_18;
  wire raw_s_c0_19, raw_c_c0_19;
  wire raw_s_c0_20, raw_c_c0_20;
  wire d0_s_c0_21, d0_c_c0_21;
  wire d1_s_c0_22, d1_c_c0_22;
  wire d1_s_c0_23, d1_c_c0_23;
  wire d2_s_c0_24, d2_c_c0_24;
  wire d2_s_c0_25, d2_c_c0_25;
  wire d3_s_c0_26, d3_c_c0_26;
  wire d3_s_c0_27, d3_c_c0_27;
  wire d4_s_c0_28, d4_c_c0_28;
  wire d5_s_c0_29, d5_c_c0_29;
  wire d6_s_c0_30, d6_c_c0_30;
  wire d0_s_c1_31, d0_c_c1_31;
  wire d1_s_c1_32, d1_c_c1_32;
  wire d1_s_c1_33, d1_c_c1_33;
  wire d1_s_c1_34, d1_c_c1_34;
  wire d1_s_c1_35, d1_c_c1_35;
  wire d2_s_c1_36, d2_c_c1_36;
  wire d2_s_c1_37, d2_c_c1_37;
  wire d2_s_c1_38, d2_c_c1_38;
  wire d3_s_c1_39, d3_c_c1_39;
  wire d3_s_c1_40, d3_c_c1_40;
  wire d4_s_c1_41, d4_c_c1_41;
  wire d4_s_c1_42, d4_c_c1_42;
  wire d5_s_c1_43, d5_c_c1_43;
  wire d6_s_c1_44, d6_c_c1_44;
  wire d7_s_c1_45, d7_c_c1_45;
  wire d0_s_c2_46, d0_c_c2_46;
  wire d1_s_c2_47, d1_c_c2_47;
  wire d1_s_c2_48, d1_c_c2_48;
  wire d2_s_c2_49, d2_c_c2_49;
  wire d3_s_c2_50, d3_c_c2_50;
  wire d4_s_c2_51, d4_c_c2_51;
  wire d5_s_c2_52, d5_c_c2_52;
  wire d0_s_c3_53, d0_c_c3_53;
  wire d1_s_c3_54, d1_c_c3_54;
  wire d3_s_c3_55, d3_c_c3_55;
  wire d0_s_c4_56, d0_c_c4_56;
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
  fa u_c0_raw_triple_raw_s_c0_10(.a(x[30]), .b(x[31]), .cin(x[32]), .sum(raw_s_c0_10), .cout(raw_c_c0_10));
  fa u_c0_raw_triple_raw_s_c0_11(.a(x[33]), .b(x[34]), .cin(x[35]), .sum(raw_s_c0_11), .cout(raw_c_c0_11));
  fa u_c0_raw_triple_raw_s_c0_12(.a(x[36]), .b(x[37]), .cin(x[38]), .sum(raw_s_c0_12), .cout(raw_c_c0_12));
  fa u_c0_raw_triple_raw_s_c0_13(.a(x[39]), .b(x[40]), .cin(x[41]), .sum(raw_s_c0_13), .cout(raw_c_c0_13));
  fa u_c0_raw_triple_raw_s_c0_14(.a(x[42]), .b(1'b1), .cin(1'b1), .sum(raw_s_c0_14), .cout(raw_c_c0_14));
  fa u_c0_raw_triple_raw_s_c0_15(.a(1'b1), .b(1'b1), .cin(1'b1), .sum(raw_s_c0_15), .cout(raw_c_c0_15));
  fa u_c0_raw_triple_raw_s_c0_16(.a(1'b1), .b(1'b1), .cin(1'b1), .sum(raw_s_c0_16), .cout(raw_c_c0_16));
  fa u_c0_raw_triple_raw_s_c0_17(.a(1'b1), .b(1'b1), .cin(1'b0), .sum(raw_s_c0_17), .cout(raw_c_c0_17));
  fa u_c0_raw_triple_raw_s_c0_18(.a(1'b0), .b(1'b0), .cin(1'b0), .sum(raw_s_c0_18), .cout(raw_c_c0_18));
  fa u_c0_raw_triple_raw_s_c0_19(.a(1'b0), .b(1'b0), .cin(1'b0), .sum(raw_s_c0_19), .cout(raw_c_c0_19));
  fa u_c0_raw_triple_raw_s_c0_20(.a(1'b0), .b(1'b0), .cin(1'b0), .sum(raw_s_c0_20), .cout(raw_c_c0_20));
  fa u_c0_d0_triple_d0_s_c0_21(.a(raw_s_c0_0), .b(raw_s_c0_1), .cin(raw_s_c0_2), .sum(d0_s_c0_21), .cout(d0_c_c0_21));
  fa u_c0_d1_triple_d1_s_c0_22(.a(d0_s_c0_21), .b(raw_s_c0_3), .cin(raw_s_c0_4), .sum(d1_s_c0_22), .cout(d1_c_c0_22));
  fa u_c0_d1_triple_d1_s_c0_23(.a(raw_s_c0_5), .b(raw_s_c0_6), .cin(raw_s_c0_7), .sum(d1_s_c0_23), .cout(d1_c_c0_23));
  fa u_c0_d2_triple_d2_s_c0_24(.a(d1_s_c0_22), .b(d1_s_c0_23), .cin(raw_s_c0_8), .sum(d2_s_c0_24), .cout(d2_c_c0_24));
  fa u_c0_d2_triple_d2_s_c0_25(.a(raw_s_c0_9), .b(raw_s_c0_10), .cin(raw_s_c0_11), .sum(d2_s_c0_25), .cout(d2_c_c0_25));
  fa u_c0_d3_triple_d3_s_c0_26(.a(d2_s_c0_24), .b(d2_s_c0_25), .cin(raw_s_c0_12), .sum(d3_s_c0_26), .cout(d3_c_c0_26));
  fa u_c0_d3_triple_d3_s_c0_27(.a(raw_s_c0_13), .b(raw_s_c0_14), .cin(raw_s_c0_15), .sum(d3_s_c0_27), .cout(d3_c_c0_27));
  fa u_c0_d4_triple_d4_s_c0_28(.a(d3_s_c0_26), .b(d3_s_c0_27), .cin(raw_s_c0_16), .sum(d4_s_c0_28), .cout(d4_c_c0_28));
  fa u_c0_d5_triple_d5_s_c0_29(.a(d4_s_c0_28), .b(raw_s_c0_17), .cin(raw_s_c0_18), .sum(d5_s_c0_29), .cout(d5_c_c0_29));
  fa u_c0_d6_triple_d6_s_c0_30(.a(d5_s_c0_29), .b(raw_s_c0_19), .cin(raw_s_c0_20), .sum(d6_s_c0_30), .cout(d6_c_c0_30));
  fa u_c1_d0_triple_d0_s_c1_31(.a(raw_c_c0_0), .b(raw_c_c0_1), .cin(raw_c_c0_2), .sum(d0_s_c1_31), .cout(d0_c_c1_31));
  fa u_c1_d1_triple_d1_s_c1_32(.a(d0_s_c1_31), .b(raw_c_c0_3), .cin(raw_c_c0_4), .sum(d1_s_c1_32), .cout(d1_c_c1_32));
  fa u_c1_d1_triple_d1_s_c1_33(.a(raw_c_c0_5), .b(raw_c_c0_6), .cin(raw_c_c0_7), .sum(d1_s_c1_33), .cout(d1_c_c1_33));
  fa u_c1_d1_triple_d1_s_c1_34(.a(raw_c_c0_8), .b(raw_c_c0_9), .cin(raw_c_c0_10), .sum(d1_s_c1_34), .cout(d1_c_c1_34));
  fa u_c1_d1_triple_d1_s_c1_35(.a(raw_c_c0_11), .b(raw_c_c0_12), .cin(raw_c_c0_13), .sum(d1_s_c1_35), .cout(d1_c_c1_35));
  fa u_c1_d2_triple_d2_s_c1_36(.a(d1_s_c1_32), .b(d1_s_c1_33), .cin(d1_s_c1_34), .sum(d2_s_c1_36), .cout(d2_c_c1_36));
  fa u_c1_d2_triple_d2_s_c1_37(.a(d1_s_c1_35), .b(raw_c_c0_14), .cin(raw_c_c0_15), .sum(d2_s_c1_37), .cout(d2_c_c1_37));
  fa u_c1_d2_triple_d2_s_c1_38(.a(raw_c_c0_16), .b(raw_c_c0_17), .cin(raw_c_c0_18), .sum(d2_s_c1_38), .cout(d2_c_c1_38));
  fa u_c1_d3_triple_d3_s_c1_39(.a(d2_s_c1_36), .b(d2_s_c1_37), .cin(d2_s_c1_38), .sum(d3_s_c1_39), .cout(d3_c_c1_39));
  fa u_c1_d3_triple_d3_s_c1_40(.a(raw_c_c0_19), .b(raw_c_c0_20), .cin(d0_c_c0_21), .sum(d3_s_c1_40), .cout(d3_c_c1_40));
  fa u_c1_d4_triple_d4_s_c1_41(.a(d3_s_c1_39), .b(d3_s_c1_40), .cin(d1_c_c0_22), .sum(d4_s_c1_41), .cout(d4_c_c1_41));
  fa u_c1_d4_triple_d4_s_c1_42(.a(d1_c_c0_23), .b(d2_c_c0_24), .cin(d2_c_c0_25), .sum(d4_s_c1_42), .cout(d4_c_c1_42));
  fa u_c1_d5_triple_d5_s_c1_43(.a(d4_s_c1_41), .b(d4_s_c1_42), .cin(d3_c_c0_26), .sum(d5_s_c1_43), .cout(d5_c_c1_43));
  fa u_c1_d6_triple_d6_s_c1_44(.a(d5_s_c1_43), .b(d3_c_c0_27), .cin(d4_c_c0_28), .sum(d6_s_c1_44), .cout(d6_c_c1_44));
  fa u_c1_d7_triple_d7_s_c1_45(.a(d6_s_c1_44), .b(d5_c_c0_29), .cin(d6_c_c0_30), .sum(d7_s_c1_45), .cout(d7_c_c1_45));
  fa u_c2_d0_triple_d0_s_c2_46(.a(d0_c_c1_31), .b(d1_c_c1_32), .cin(d1_c_c1_33), .sum(d0_s_c2_46), .cout(d0_c_c2_46));
  fa u_c2_d1_triple_d1_s_c2_47(.a(d0_s_c2_46), .b(d1_c_c1_34), .cin(d1_c_c1_35), .sum(d1_s_c2_47), .cout(d1_c_c2_47));
  fa u_c2_d1_triple_d1_s_c2_48(.a(d2_c_c1_36), .b(d2_c_c1_37), .cin(d2_c_c1_38), .sum(d1_s_c2_48), .cout(d1_c_c2_48));
  fa u_c2_d2_triple_d2_s_c2_49(.a(d1_s_c2_47), .b(d1_s_c2_48), .cin(d3_c_c1_39), .sum(d2_s_c2_49), .cout(d2_c_c2_49));
  fa u_c2_d3_triple_d3_s_c2_50(.a(d2_s_c2_49), .b(d3_c_c1_40), .cin(d4_c_c1_41), .sum(d3_s_c2_50), .cout(d3_c_c2_50));
  fa u_c2_d4_triple_d4_s_c2_51(.a(d3_s_c2_50), .b(d4_c_c1_42), .cin(d5_c_c1_43), .sum(d4_s_c2_51), .cout(d4_c_c2_51));
  fa u_c2_d5_triple_d5_s_c2_52(.a(d4_s_c2_51), .b(d6_c_c1_44), .cin(d7_c_c1_45), .sum(d5_s_c2_52), .cout(d5_c_c2_52));
  fa u_c3_d0_triple_d0_s_c3_53(.a(d0_c_c2_46), .b(d1_c_c2_47), .cin(d1_c_c2_48), .sum(d0_s_c3_53), .cout(d0_c_c3_53));
  fa u_c3_d1_triple_d1_s_c3_54(.a(d0_s_c3_53), .b(d2_c_c2_49), .cin(d3_c_c2_50), .sum(d1_s_c3_54), .cout(d1_c_c3_54));
  fa u_c3_d3_triple_d3_s_c3_55(.a(d1_s_c3_54), .b(d4_c_c2_51), .cin(d5_c_c2_52), .sum(d3_s_c3_55), .cout(d3_c_c3_55));
  fa u_c4_d0_triple_d0_s_c4_56(.a(d0_c_c3_53), .b(d1_c_c3_54), .cin(d3_c_c3_55), .sum(d0_s_c4_56), .cout(d0_c_c4_56));

  // -------- HW bits after CSA (single-rail) --------
  wire hw_0 = d6_s_c0_30;
  wire hw_1 = d7_s_c1_45;
  wire hw_2 = d5_s_c2_52;
  wire hw_3 = d3_s_c3_55;
  wire hw_4 = d0_s_c4_56;
  wire hw_5 = d0_c_c4_56;

  // Threshold constant bits (th_N - 1)
  wire T0 = 1'b1;
  wire T1 = 1'b1;
  wire T2 = 1'b1;
  wire T3 = 1'b1;
  wire T4 = 1'b1;

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
  fa u_th_4(.a(hw_4), .b(T4), .cin(c2_4), .sum(s2_4), .cout(c2_5));
  wire s2_5, c2_6;
  fa u_th_5(.a(hw_5), .b(1'b0), .cin(c2_5), .sum(s2_5), .cout(c2_6));
  wire c2_m = c2_6;

  assign maj = c2_m;
endmodule

// FA count (baseline STRICT, scaffold) for n=43: CSA=57, CPA(th)=6, total=63