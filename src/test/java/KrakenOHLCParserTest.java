import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

public class KrakenOHLCParserTest {

  Parser parser = new KrakenOHLCParser();

//  @Test
//  public void testParserWithExampleInput() {
//    PriceData result = parser.parse("[[1608772980,\"0.110826\",\"0.110826\",\"0.110826\",\"0.110826\",\"0.000000\",\"0.00000000\",0],[1608773040,\"0.110806\",\"0.110806\",\"0.110798\",\"0.110798\",\"0.110798\",\"4470.69772860\",2]]");
//    OHLCCandle[] expectedData =
//        {new OHLCCandle(0.110826, 0.110826, 0.110826, 0.110826),
//         new OHLCCandle(0.110806, 0.110806, 0.110798, 0.110798)};
//    PriceData expected = new PriceData("", expectedData);
//    Assertions.assertEquals(result, expected);
//  }

  @Test
  public void testParserWithExampleInputFromKraken() {
    PriceData result = parser.parse("{\"error\":[],\"result\":{\"ADAEUR\":[[1608772980,\"0.110826\",\"0.110826\",\"0.110826\",\"0.110826\",\"0.000000\",\"0.00000000\",0],[1608773040,\"0.110806\",\"0.110806\",\"0.110798\",\"0.110798\",\"0.110798\",\"4470.69772860\",2]],\"last\":1608816060}}");
    OHLCCandle[] expectedData =
        {new OHLCCandle(0.110826, 0.110826, 0.110826, 0.110826),
            new OHLCCandle(0.110806, 0.110806, 0.110798, 0.110798)};
    PriceData expected = new PriceData("ADAEUR", expectedData);
    Assertions.assertEquals(expected, result);
  }
}
