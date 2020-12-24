import java.util.Objects;

public class OHLCCandle {

  private final double open, high, low, close;

  public OHLCCandle(double open, double high, double low, double close) {
    this.open = open;
    this.high = high;
    this.low = low;
    this.close = close;
  }

  public double open() {
    return open;
  }

  public double high() {
    return high;
  }

  public double low() {
    return low;
  }

  public double close() {
    return close;
  }

  public boolean crossedTargetPrice(double target) {
    return low <= target && target <= high;
  }

  public Colour getColour() {
    if (close > open) {
      return Colour.GREEN;
    } else if (close < open) {
      return Colour.RED;
    } else {
      return Colour.NONE;
    }
  }

  public enum Colour {
    RED,
    GREEN,
    NONE
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    OHLCCandle that = (OHLCCandle) o;
    return Double.compare(that.open, open) == 0
        && Double.compare(that.high, high) == 0
        && Double.compare(that.low, low) == 0
        && Double.compare(that.close, close) == 0;
  }

  @Override
  public int hashCode() {
    return Objects.hash(open, high, low, close);
  }
}
