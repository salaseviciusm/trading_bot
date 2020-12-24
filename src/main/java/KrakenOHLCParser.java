import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class KrakenOHLCParser implements Parser {

  public final static String OHLCPattern = "\\[[^\\[]([^]\\[]*,?){8}]";

  /* Takes in OHLC data from Kraken in the JSON form and deserializes it. */
  public PriceData parse (String input) {
    Matcher s = Pattern.compile("\"[A-Z]*\"").matcher(input);
    s.find();
    String symbol = s.group().replaceAll("\"", "");

    List<OHLCCandle> result = new ArrayList<>();
    Matcher m = Pattern.compile(OHLCPattern).matcher(input);
    while (m.find()) {
      String match = m.group().replaceAll("[\\[\\]\"]", "");
      String[] values = match.split(",");
      result.add(new OHLCCandle(Double.parseDouble(values[1]),
          Double.parseDouble(values[2]),
          Double.parseDouble(values[3]),
          Double.parseDouble(values[4])));
    }
    return new PriceData(symbol, result.toArray(new OHLCCandle[0]));
  }

}
