module folded_bias_13(input [12:0] x, output maj);
  wire K0, d0_c_c0_4, d0_c_c1_7, d0_c_c2_10, d0_s_c0_4, d0_s_c1_7, d0_s_c2_10, d1_c_c0_5, d1_c_c1_8, d1_s_c0_5, d1_s_c1_8, d3_c_c1_9, d3_p_c_c0_6, d3_p_s_c0_6, d3_s_c1_9, raw_c_c0_0, raw_c_c0_1, raw_c_c0_2, raw_c_c0_3, raw_s_c0_0, raw_s_c0_1, raw_s_c0_2, raw_s_c0_3;
  assign K0 = 1'b1;
  fa u0(.a(x[0]), .b(x[1]), .cin(x[2]), .sum(raw_s_c0_0), .cout(raw_c_c0_0));
  fa u1(.a(x[3]), .b(x[4]), .cin(x[5]), .sum(raw_s_c0_1), .cout(raw_c_c0_1));
  fa u2(.a(x[6]), .b(x[7]), .cin(x[8]), .sum(raw_s_c0_2), .cout(raw_c_c0_2));
  fa u3(.a(x[9]), .b(x[10]), .cin(x[11]), .sum(raw_s_c0_3), .cout(raw_c_c0_3));
  fa u4(.a(raw_s_c0_0), .b(raw_s_c0_1), .cin(raw_s_c0_2), .sum(d0_s_c0_4), .cout(d0_c_c0_4));
  fa u5(.a(d0_s_c0_4), .b(raw_s_c0_3), .cin(x[12]), .sum(d1_s_c0_5), .cout(d1_c_c0_5));
  fa u6(.a(d1_s_c0_5), .b(K0), .cin(1'b0), .sum(d3_p_s_c0_6), .cout(d3_p_c_c0_6));
  fa u7(.a(raw_c_c0_0), .b(raw_c_c0_1), .cin(raw_c_c0_2), .sum(d0_s_c1_7), .cout(d0_c_c1_7));
  fa u8(.a(d0_s_c1_7), .b(raw_c_c0_3), .cin(d0_c_c0_4), .sum(d1_s_c1_8), .cout(d1_c_c1_8));
  fa u9(.a(d1_s_c1_8), .b(d1_c_c0_5), .cin(d3_p_c_c0_6), .sum(d3_s_c1_9), .cout(d3_c_c1_9));
  fa u10(.a(d0_c_c1_7), .b(d1_c_c1_8), .cin(d3_c_c1_9), .sum(d0_s_c2_10), .cout(d0_c_c2_10));
  assign maj = d0_c_c2_10;
endmodule

module fa(input a, b, cin, output sum, cout);
  assign sum = a ^ b ^ cin;
  assign cout = (a & b) | (a & cin) | (b & cin);
endmodule
