module folded_bias_7(input [6:0] x, output maj);
  wire d0_c_c0_2, d0_c_c1_3, d0_s_c0_2, d0_s_c1_3, raw_c_c0_0, raw_c_c0_1, raw_s_c0_0, raw_s_c0_1;
  fa u0(.a(x[0]), .b(x[1]), .cin(x[2]), .sum(raw_s_c0_0), .cout(raw_c_c0_0));
  fa u1(.a(x[3]), .b(x[4]), .cin(x[5]), .sum(raw_s_c0_1), .cout(raw_c_c0_1));
  fa u2(.a(raw_s_c0_0), .b(raw_s_c0_1), .cin(x[6]), .sum(d0_s_c0_2), .cout(d0_c_c0_2));
  fa u3(.a(raw_c_c0_0), .b(raw_c_c0_1), .cin(d0_c_c0_2), .sum(d0_s_c1_3), .cout(d0_c_c1_3));
  assign maj = d0_c_c1_3;
endmodule

module fa(input a, b, cin, output sum, cout);
  assign sum = a ^ b ^ cin;
  assign cout = (a & b) | (a & cin) | (b & cin);
endmodule
