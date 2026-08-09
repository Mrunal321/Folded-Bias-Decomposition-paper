module folded_bias_5(input [4:0] x, output maj);
  wire K0, d0_c_c0_1, d0_c_c1_3, d0_s_c0_1, d0_s_c1_3, d2_p_c_c0_2, d2_p_s_c0_2, raw_c_c0_0, raw_s_c0_0;
  assign K0 = 1'b1;
  fa u0(.a(x[0]), .b(x[1]), .cin(x[2]), .sum(raw_s_c0_0), .cout(raw_c_c0_0));
  fa u1(.a(raw_s_c0_0), .b(x[3]), .cin(x[4]), .sum(d0_s_c0_1), .cout(d0_c_c0_1));
  fa u2(.a(d0_s_c0_1), .b(K0), .cin(1'b0), .sum(d2_p_s_c0_2), .cout(d2_p_c_c0_2));
  fa u3(.a(raw_c_c0_0), .b(d0_c_c0_1), .cin(d2_p_c_c0_2), .sum(d0_s_c1_3), .cout(d0_c_c1_3));
  assign maj = d0_c_c1_3;
endmodule

module fa(input a, b, cin, output sum, cout);
  assign sum = a ^ b ^ cin;
  assign cout = (a & b) | (a & cin) | (b & cin);
endmodule
