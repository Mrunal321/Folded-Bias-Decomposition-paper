module folded_bias_25(input [24:0] x, output maj);
  wire K0, K1, d0_c_c0_8, d0_c_c1_13, d0_c_c2_20, d0_c_c3_23, d0_s_c0_8, d0_s_c1_13, d0_s_c2_20, d0_s_c3_23, d1_c_c0_9, d1_c_c1_14, d1_c_c2_21, d1_s_c0_9, d1_s_c1_14, d1_s_c2_21, d2_c_c0_10, d2_c_c1_15, d2_c_c1_16, d2_s_c0_10, d2_s_c1_15, d2_s_c1_16, d3_c_c0_11, d3_c_c1_17, d3_c_c2_22, d3_s_c0_11, d3_s_c1_17, d3_s_c2_22, d4_c_c1_18, d4_s_c1_18, d5_p_c_c0_12, d5_p_s_c0_12, d6_p_c_c1_19, d6_p_s_c1_19, raw_c_c0_0, raw_c_c0_1, raw_c_c0_2, raw_c_c0_3, raw_c_c0_4, raw_c_c0_5, raw_c_c0_6, raw_c_c0_7, raw_s_c0_0, raw_s_c0_1, raw_s_c0_2, raw_s_c0_3, raw_s_c0_4, raw_s_c0_5, raw_s_c0_6, raw_s_c0_7;
  assign K0 = 1'b1;
  assign K1 = 1'b1;
  fa u0(.a(x[0]), .b(x[1]), .cin(x[2]), .sum(raw_s_c0_0), .cout(raw_c_c0_0));
  fa u1(.a(x[3]), .b(x[4]), .cin(x[5]), .sum(raw_s_c0_1), .cout(raw_c_c0_1));
  fa u2(.a(x[6]), .b(x[7]), .cin(x[8]), .sum(raw_s_c0_2), .cout(raw_c_c0_2));
  fa u3(.a(x[9]), .b(x[10]), .cin(x[11]), .sum(raw_s_c0_3), .cout(raw_c_c0_3));
  fa u4(.a(x[12]), .b(x[13]), .cin(x[14]), .sum(raw_s_c0_4), .cout(raw_c_c0_4));
  fa u5(.a(x[15]), .b(x[16]), .cin(x[17]), .sum(raw_s_c0_5), .cout(raw_c_c0_5));
  fa u6(.a(x[18]), .b(x[19]), .cin(x[20]), .sum(raw_s_c0_6), .cout(raw_c_c0_6));
  fa u7(.a(x[21]), .b(x[22]), .cin(x[23]), .sum(raw_s_c0_7), .cout(raw_c_c0_7));
  fa u8(.a(raw_s_c0_0), .b(raw_s_c0_1), .cin(raw_s_c0_2), .sum(d0_s_c0_8), .cout(d0_c_c0_8));
  fa u9(.a(d0_s_c0_8), .b(raw_s_c0_3), .cin(raw_s_c0_4), .sum(d1_s_c0_9), .cout(d1_c_c0_9));
  fa u10(.a(d1_s_c0_9), .b(raw_s_c0_5), .cin(raw_s_c0_6), .sum(d2_s_c0_10), .cout(d2_c_c0_10));
  fa u11(.a(d2_s_c0_10), .b(raw_s_c0_7), .cin(x[24]), .sum(d3_s_c0_11), .cout(d3_c_c0_11));
  fa u12(.a(d3_s_c0_11), .b(K0), .cin(1'b0), .sum(d5_p_s_c0_12), .cout(d5_p_c_c0_12));
  fa u13(.a(raw_c_c0_0), .b(raw_c_c0_1), .cin(raw_c_c0_2), .sum(d0_s_c1_13), .cout(d0_c_c1_13));
  fa u14(.a(d0_s_c1_13), .b(raw_c_c0_3), .cin(raw_c_c0_4), .sum(d1_s_c1_14), .cout(d1_c_c1_14));
  fa u15(.a(d1_s_c1_14), .b(raw_c_c0_5), .cin(raw_c_c0_6), .sum(d2_s_c1_15), .cout(d2_c_c1_15));
  fa u16(.a(raw_c_c0_7), .b(d0_c_c0_8), .cin(d1_c_c0_9), .sum(d2_s_c1_16), .cout(d2_c_c1_16));
  fa u17(.a(d2_s_c1_15), .b(d2_s_c1_16), .cin(d2_c_c0_10), .sum(d3_s_c1_17), .cout(d3_c_c1_17));
  fa u18(.a(d3_s_c1_17), .b(d3_c_c0_11), .cin(d5_p_c_c0_12), .sum(d4_s_c1_18), .cout(d4_c_c1_18));
  fa u19(.a(d4_s_c1_18), .b(K1), .cin(1'b0), .sum(d6_p_s_c1_19), .cout(d6_p_c_c1_19));
  fa u20(.a(d0_c_c1_13), .b(d1_c_c1_14), .cin(d2_c_c1_15), .sum(d0_s_c2_20), .cout(d0_c_c2_20));
  fa u21(.a(d0_s_c2_20), .b(d2_c_c1_16), .cin(d3_c_c1_17), .sum(d1_s_c2_21), .cout(d1_c_c2_21));
  fa u22(.a(d1_s_c2_21), .b(d4_c_c1_18), .cin(d6_p_c_c1_19), .sum(d3_s_c2_22), .cout(d3_c_c2_22));
  fa u23(.a(d0_c_c2_20), .b(d1_c_c2_21), .cin(d3_c_c2_22), .sum(d0_s_c3_23), .cout(d0_c_c3_23));
  assign maj = d0_c_c3_23;
endmodule

module fa(input a, b, cin, output sum, cout);
  assign sum = a ^ b ^ cin;
  assign cout = (a & b) | (a & cin) | (b & cin);
endmodule
