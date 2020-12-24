public class SMA implements Indicator {

  private final int periods; // Range of SMA in days

  public SMA(int periods) {
    this.periods = periods;
  }

  @Override
  public Signal apply(PriceData priceData) {
    double sma = priceData.getCloses().reduce((double) 0, Double::sum) / periods;

    OHLCCandle latestPrice = priceData.latestPrice();
    if (latestPrice.crossedTargetPrice(sma)) {
      return switch (latestPrice.getColour()) {
        case GREEN -> Signal.BUY;
        case RED -> Signal.SELL;
        case NONE -> Signal.HOLD;
      };
    }
    return Signal.HOLD;
  }
}
