import java.util.Arrays;
import java.util.stream.Stream;

public class PriceData {

  private final String symbol;
  private OHLCCandle[] priceData;

  public PriceData(String symbol, OHLCCandle[] priceData) {
    this.symbol = symbol;
    this.priceData = priceData;
  }

  public OHLCCandle latestPrice() {
    return priceData[priceData.length - 1];
  }

  public Stream<Double> getCloses() {
    return Arrays.stream(priceData).map(OHLCCandle::close);
  }

  public int getLength() {
    return priceData.length;
  }
}
