import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

public class OHLCParserTest {
  @Test
  public void testParserWithExampleInput() {
    OHLCCandle[] result = OHLCParser.parse("[[1608772980,\"0.110826\",\"0.110826\",\"0.110826\",\"0.110826\",\"0.000000\",\"0.00000000\",0],[1608773040,\"0.110806\",\"0.110806\",\"0.110798\",\"0.110798\",\"0.110798\",\"4470.69772860\",2]]");
    OHLCCandle[] expected =
        {new OHLCCandle(0.110826, 0.110826, 0.110826, 0.110826),
         new OHLCCandle(0.110806, 0.110806, 0.110798, 0.110798)};
    Assertions.assertArrayEquals(result, expected);
  }

  @Test
  public void testParserWithExampleInputFromKraken() {
    OHLCCandle[] result = OHLCParser.parse("{\"error\":[],\"result\":{\"ADAEUR\":[[1608772980,\"0.110826\",\"0.110826\",\"0.110826\",\"0.110826\",\"0.000000\",\"0.00000000\",0],[1608773040,\"0.110806\",\"0.110806\",\"0.110798\",\"0.110798\",\"0.110798\",\"4470.69772860\",2]],\"last\":1608816060}}");
    OHLCCandle[] expected =
        {new OHLCCandle(0.110826, 0.110826, 0.110826, 0.110826),
            new OHLCCandle(0.110806, 0.110806, 0.110798, 0.110798)};
    Assertions.assertArrayEquals(result, expected);
  }
}
