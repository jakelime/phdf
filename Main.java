import phdf_j.Phdf;
import phdf_j.JFileReader;

public class Main {

    public static void main(String[] args) {

        JFileReader reader = new JFileReader(
                "/Users/jli8/activedir/200-phdf/resources/testfilewriter-2047225563688979.txt");
        String jsonString = reader.read();
        System.out.println("jsonString length is " + jsonString.length());

        // Initialize the CLI tool
        Phdf processor = new Phdf();
        // To debug CLI: getCommand, setCommand, etc.
        // processor.appendUserInputToCommand(jsonString, );
        // System.out.println(processor.getCommand());
        // ## These paths are customised for use in Jake ##
        processor.setPythonPath("/Users/jli8/miniconda3/envs/p311/bin/python"); // path for JakeMBP
        processor.setCliPath("/Users/jli8/activedir/200-phdf/cli.py"); // path for JakeMBP
        processor.initCommand();

        // Run the CLI tool
        // processor.run(jsonString, "/Users/jli8/Downloads"); // Unfortunately, we get error=7, Argument list too long
        // processor.run("{\"partId1\": {\"R00C00\": { \"site1\":{\"aTB_0\": \"0.0\"}}}}", "/Users/jli8/Downloads");
        processor.run("/Users/jli8/activedir/200-phdf/resources/testfilewriter-2047225563688979.txt", "/Users/jli8/Downloads");
    }

}
