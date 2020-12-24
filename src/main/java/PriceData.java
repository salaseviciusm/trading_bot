import java.util.Arrays;
import java.util.Objects;
import java.util.stream.Stream;

public class PriceData {

  private final String symbol;
  private final OHLCCandle[] priceData;

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

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    PriceData priceData1 = (PriceData) o;
    return symbol.equals(priceData1.symbol) && Arrays
        .equals(priceData, priceData1.priceData);
  }

  @Override
  public int hashCode() {
    int result = Objects.hash(symbol);
    result = 31 * result + Arrays.hashCode(priceData);
    return result;
  }

  @Override
  public String toString() {
    return "PriceData{" +
        "symbol='" + symbol + '\'' +
        ", priceData=" + Arrays.toString(priceData) +
        '}';
  }
}
