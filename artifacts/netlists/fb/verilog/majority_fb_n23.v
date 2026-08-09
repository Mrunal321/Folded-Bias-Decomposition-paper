module folded_bias_23(input [22:0] x, output maj);
  wire K2, d0_c_c0_7, d0_c_c1_11, d0_c_c2_16, d0_c_c3_19, d0_s_c0_7, d0_s_c1_11, d0_s_c2_16, d0_s_c3_19, d1_c_c0_8, d1_c_c1_12, d1_c_c2_17, d1_s_c0_8, d1_s_c1_12, d1_s_c2_17, d2_c_c0_9, d2_c_c1_13, d2_s_c0_9, d2_s_c1_13, d3_c_c0_10, d3_c_c1_14, d3_p_c_c2_18, d3_p_s_c2_18, d3_s_c0_10, d3_s_c1_14, d4_c_c1_15, d4_s_c1_15, raw_c_c0_0, raw_c_c0_1, raw_c_c0_2, raw_c_c0_3, raw_c_c0_4, raw_c_c0_5, raw_c_c0_6, raw_s_c0_0, raw_s_c0_1, raw_s_c0_2, raw_s_c0_3, raw_s_c0_4, raw_s_c0_5, raw_s_c0_6;
  assign K2 = 1'b1;
  fa u0(.a(x[0]), .b(x[1]), .cin(x[2]), .sum(raw_s_c0_0), .cout(raw_c_c0_0));
  fa u1(.a(x[3]), .b(x[4]), .cin(x[5]), .sum(raw_s_c0_1), .cout(raw_c_c0_1));
  fa u2(.a(x[6]), .b(x[7]), .cin(x[8]), .sum(raw_s_c0_2), .cout(raw_c_c0_2));
  fa u3(.a(x[9]), .b(x[10]), .cin(x[11]), .sum(raw_s_c0_3), .cout(raw_c_c0_3));
  fa u4(.a(x[12]), .b(x[13]), .cin(x[14]), .sum(raw_s_c0_4), .cout(raw_c_c0_4));
  fa u5(.a(x[15]), .b(x[16]), .cin(x[17]), .sum(raw_s_c0_5), .cout(raw_c_c0_5));
  fa u6(.a(x[18]), .b(x[19]), .cin(x[20]), .sum(raw_s_c0_6), .cout(raw_c_c0_6));
  fa u7(.a(raw_s_c0_0), .b(raw_s_c0_1), .cin(raw_s_c0_2), .sum(d0_s_c0_7), .cout(d0_c_c0_7));
  fa u8(.a(d0_s_c0_7), .b(raw_s_c0_3), .cin(raw_s_c0_4), .sum(d1_s_c0_8), .cout(d1_c_c0_8));
  fa u9(.a(d1_s_c0_8), .b(raw_s_c0_5), .cin(raw_s_c0_6), .sum(d2_s_c0_9), .cout(d2_c_c0_9));
  fa u10(.a(d2_s_c0_9), .b(x[21]), .cin(x[22]), .sum(d3_s_c0_10), .cout(d3_c_c0_10));
  fa u11(.a(raw_c_c0_0), .b(raw_c_c0_1), .cin(raw_c_c0_2), .sum(d0_s_c1_11), .cout(d0_c_c1_11));
  fa u12(.a(d0_s_c1_11), .b(raw_c_c0_3), .cin(raw_c_c0_4), .sum(d1_s_c1_12), .cout(d1_c_c1_12));
  fa u13(.a(d1_s_c1_12), .b(raw_c_c0_5), .cin(raw_c_c0_6), .sum(d2_s_c1_13), .cout(d2_c_c1_13));
  fa u14(.a(d2_s_c1_13), .b(d0_c_c0_7), .cin(d1_c_c0_8), .sum(d3_s_c1_14), .cout(d3_c_c1_14));
  fa u15(.a(d3_s_c1_14), .b(d2_c_c0_9), .cin(d3_c_c0_10), .sum(d4_s_c1_15), .cout(d4_c_c1_15));
  fa u16(.a(d0_c_c1_11), .b(d1_c_c1_12), .cin(d2_c_c1_13), .sum(d0_s_c2_16), .cout(d0_c_c2_16));
  fa u17(.a(d0_s_c2_16), .b(d3_c_c1_14), .cin(d4_c_c1_15), .sum(d1_s_c2_17), .cout(d1_c_c2_17));
  fa u18(.a(d1_s_c2_17), .b(K2), .cin(1'b0), .sum(d3_p_s_c2_18), .cout(d3_p_c_c2_18));
  fa u19(.a(d0_c_c2_16), .b(d1_c_c2_17), .cin(d3_p_c_c2_18), .sum(d0_s_c3_19), .cout(d0_c_c3_19));
  assign maj = d0_c_c3_19;
endmodule

module fa(input a, b, cin, output sum, cout);
  assign sum = a ^ b ^ cin;
  assign cout = (a & b) | (a & cin) | (b & cin);
endmodule
