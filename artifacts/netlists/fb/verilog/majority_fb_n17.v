module folded_bias_17(input [16:0] x, output maj);
  wire K0, K1, K2, d0_c_c0_5, d0_c_c1_9, d0_c_c2_14, d0_c_c3_17, d0_s_c0_5, d0_s_c1_9, d0_s_c2_14, d0_s_c3_17, d1_c_c0_6, d1_c_c1_10, d1_c_c2_15, d1_s_c0_6, d1_s_c1_10, d1_s_c2_15, d2_c_c0_7, d2_c_c1_11, d2_s_c0_7, d2_s_c1_11, d3_c_c1_12, d3_p_c_c2_16, d3_p_s_c2_16, d3_s_c1_12, d4_p_c_c0_8, d4_p_s_c0_8, d5_p_c_c1_13, d5_p_s_c1_13, raw_c_c0_0, raw_c_c0_1, raw_c_c0_2, raw_c_c0_3, raw_c_c0_4, raw_s_c0_0, raw_s_c0_1, raw_s_c0_2, raw_s_c0_3, raw_s_c0_4;
  assign K0 = 1'b1;
  assign K1 = 1'b1;
  assign K2 = 1'b1;
  fa u0(.a(x[0]), .b(x[1]), .cin(x[2]), .sum(raw_s_c0_0), .cout(raw_c_c0_0));
  fa u1(.a(x[3]), .b(x[4]), .cin(x[5]), .sum(raw_s_c0_1), .cout(raw_c_c0_1));
  fa u2(.a(x[6]), .b(x[7]), .cin(x[8]), .sum(raw_s_c0_2), .cout(raw_c_c0_2));
  fa u3(.a(x[9]), .b(x[10]), .cin(x[11]), .sum(raw_s_c0_3), .cout(raw_c_c0_3));
  fa u4(.a(x[12]), .b(x[13]), .cin(x[14]), .sum(raw_s_c0_4), .cout(raw_c_c0_4));
  fa u5(.a(raw_s_c0_0), .b(raw_s_c0_1), .cin(raw_s_c0_2), .sum(d0_s_c0_5), .cout(d0_c_c0_5));
  fa u6(.a(d0_s_c0_5), .b(raw_s_c0_3), .cin(raw_s_c0_4), .sum(d1_s_c0_6), .cout(d1_c_c0_6));
  fa u7(.a(d1_s_c0_6), .b(x[15]), .cin(x[16]), .sum(d2_s_c0_7), .cout(d2_c_c0_7));
  fa u8(.a(d2_s_c0_7), .b(K0), .cin(1'b0), .sum(d4_p_s_c0_8), .cout(d4_p_c_c0_8));
  fa u9(.a(raw_c_c0_0), .b(raw_c_c0_1), .cin(raw_c_c0_2), .sum(d0_s_c1_9), .cout(d0_c_c1_9));
  fa u10(.a(d0_s_c1_9), .b(raw_c_c0_3), .cin(raw_c_c0_4), .sum(d1_s_c1_10), .cout(d1_c_c1_10));
  fa u11(.a(d1_s_c1_10), .b(d0_c_c0_5), .cin(d1_c_c0_6), .sum(d2_s_c1_11), .cout(d2_c_c1_11));
  fa u12(.a(d2_s_c1_11), .b(d2_c_c0_7), .cin(d4_p_c_c0_8), .sum(d3_s_c1_12), .cout(d3_c_c1_12));
  fa u13(.a(d3_s_c1_12), .b(K1), .cin(1'b0), .sum(d5_p_s_c1_13), .cout(d5_p_c_c1_13));
  fa u14(.a(d0_c_c1_9), .b(d1_c_c1_10), .cin(d2_c_c1_11), .sum(d0_s_c2_14), .cout(d0_c_c2_14));
  fa u15(.a(d0_s_c2_14), .b(d3_c_c1_12), .cin(d5_p_c_c1_13), .sum(d1_s_c2_15), .cout(d1_c_c2_15));
  fa u16(.a(d1_s_c2_15), .b(K2), .cin(1'b0), .sum(d3_p_s_c2_16), .cout(d3_p_c_c2_16));
  fa u17(.a(d0_c_c2_14), .b(d1_c_c2_15), .cin(d3_p_c_c2_16), .sum(d0_s_c3_17), .cout(d0_c_c3_17));
  assign maj = d0_c_c3_17;
endmodule

module fa(input a, b, cin, output sum, cout);
  assign sum = a ^ b ^ cin;
  assign cout = (a & b) | (a & cin) | (b & cin);
endmodule
