import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class OHLCParser {

  public final static String pattern = "\\[[^\\[]([^]\\[]*,?){8}]";

  /* Takes in OHLC data in the form of a 2D array in chronological order.
  * Arguments come in the order:
  * Open, High, Low, Close
  */
  public static OHLCCandle[] parse (String input) {
    List<OHLCCandle> result = new ArrayList<>();
    Matcher m = Pattern.compile(pattern).matcher(input);
    while (m.find()) {
      String match = m.group().replaceAll("[\\[\\]\"]", "");
      String[] values = match.split(",");
      result.add(new OHLCCandle(Double.parseDouble(values[1]),
          Double.parseDouble(values[2]),
          Double.parseDouble(values[3]),
          Double.parseDouble(values[4])));
    }
    return result.toArray(new OHLCCandle[0]);
  }

}
