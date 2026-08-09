module parhami_2009_apc_7(input [6:0] x, output maj);
  wire APC_K2, apc_final_c1, apc_final_c2, apc_final_c3, apc_final_s0, apc_final_s1, apc_final_s2, apc_l0_a0_c1, apc_l0_a0_c2, apc_l0_a0_s0, apc_l0_a0_s1, apc_l0_a1_c1, apc_l0_a1_c2, apc_l0_a1_s0, apc_l0_a1_s1, apc_l0_a2_c1, apc_l0_a2_c2, apc_l0_a2_s0, apc_l0_a2_s1, apc_l1_a0_c1, apc_l1_a0_c2, apc_l1_a0_c3, apc_l1_a0_s0, apc_l1_a0_s1, apc_l1_a0_s2, apc_l1_a1_c1, apc_l1_a1_c2, apc_l1_a1_s0, apc_l1_a1_s1, apc_l2_a0_c1, apc_l2_a0_c2, apc_l2_a0_c3, apc_l2_a0_s0, apc_l2_a0_s1, apc_l2_a0_s2;
  assign APC_K2 = 1'b1;
  fa u0(.a(x[0]), .b(x[1]), .cin(1'b0), .sum(apc_l0_a0_s0), .cout(apc_l0_a0_c1));
  fa u1(.a(1'b0), .b(1'b0), .cin(apc_l0_a0_c1), .sum(apc_l0_a0_s1), .cout(apc_l0_a0_c2));
  fa u2(.a(x[2]), .b(x[3]), .cin(1'b0), .sum(apc_l0_a1_s0), .cout(apc_l0_a1_c1));
  fa u3(.a(1'b0), .b(1'b0), .cin(apc_l0_a1_c1), .sum(apc_l0_a1_s1), .cout(apc_l0_a1_c2));
  fa u4(.a(x[4]), .b(x[5]), .cin(1'b0), .sum(apc_l0_a2_s0), .cout(apc_l0_a2_c1));
  fa u5(.a(1'b0), .b(1'b0), .cin(apc_l0_a2_c1), .sum(apc_l0_a2_s1), .cout(apc_l0_a2_c2));
  fa u6(.a(apc_l0_a0_s0), .b(apc_l0_a1_s0), .cin(1'b0), .sum(apc_l1_a0_s0), .cout(apc_l1_a0_c1));
  fa u7(.a(apc_l0_a0_s1), .b(apc_l0_a1_s1), .cin(apc_l1_a0_c1), .sum(apc_l1_a0_s1), .cout(apc_l1_a0_c2));
  fa u8(.a(1'b0), .b(1'b0), .cin(apc_l1_a0_c2), .sum(apc_l1_a0_s2), .cout(apc_l1_a0_c3));
  fa u9(.a(apc_l0_a2_s0), .b(x[6]), .cin(1'b0), .sum(apc_l1_a1_s0), .cout(apc_l1_a1_c1));
  fa u10(.a(apc_l0_a2_s1), .b(1'b0), .cin(apc_l1_a1_c1), .sum(apc_l1_a1_s1), .cout(apc_l1_a1_c2));
  fa u11(.a(apc_l1_a0_s0), .b(apc_l1_a1_s0), .cin(1'b0), .sum(apc_l2_a0_s0), .cout(apc_l2_a0_c1));
  fa u12(.a(apc_l1_a0_s1), .b(apc_l1_a1_s1), .cin(apc_l2_a0_c1), .sum(apc_l2_a0_s1), .cout(apc_l2_a0_c2));
  fa u13(.a(apc_l1_a0_s2), .b(1'b0), .cin(apc_l2_a0_c2), .sum(apc_l2_a0_s2), .cout(apc_l2_a0_c3));
  fa u14(.a(apc_l2_a0_s0), .b(1'b0), .cin(1'b0), .sum(apc_final_s0), .cout(apc_final_c1));
  fa u15(.a(apc_l2_a0_s1), .b(1'b0), .cin(apc_final_c1), .sum(apc_final_s1), .cout(apc_final_c2));
  fa u16(.a(apc_l2_a0_s2), .b(APC_K2), .cin(apc_final_c2), .sum(apc_final_s2), .cout(apc_final_c3));
  assign maj = apc_final_c3;
endmodule

module fa(input a, b, cin, output sum, cout);
  assign sum = a ^ b ^ cin;
  assign cout = (a & b) | (a & cin) | (b & cin);
endmodule
