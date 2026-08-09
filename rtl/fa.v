// Technology-independent one-bit full adder used by generated Verilog.
module fa (
    input  wire a,
    input  wire b,
    input  wire cin,
    output wire sum,
    output wire cout
);
    assign {cout, sum} = a + b + cin;
endmodule
