import phdf_j.Phdf;
import phdf_j.JFileReader;

public class Main {

    // This is the Java entry point to call PHDF

    public static void main(String[] args) {

        // Method 1.
        // Use JSON str, pass directly to shell
        // DEPRECATED. Full data is too huge to be passed directly. We will employ method2
        JFileReader reader = new JFileReader(
                "/Users/jli8/activedir/200-phdf/resources/testfilewriter-2047225563688979.txt");
        String jsonString = reader.read();
        System.out.println("jsonString length is " + jsonString.length());


        // Method 2:
        // We use FileIO, write data into a temporary file
        // JFileWriter.write(jsonString, testfilewriter-2047225563688979.txt)


        // Initialize the PHDF object, to process the data
        Phdf processor = new Phdf();
        // ## These paths are customised for use in Jake ##
        // By default, the suffix is hardcoded (prefix is automtically determined by Java)
        processor.setPythonPath("/Users/jli8/miniconda3/envs/p311/bin/python"); // for debugging (on JakeMBP)
        processor.setCliPath("/Users/jli8/activedir/200-phdf/cli.py"); // for debugging (on JakeMBP)
         // for debugging (on JakeMBP)

        // Run PHDF

        // Using method 1
        // processor.run(jsonString, "/Users/jli8/Downloads"); // Unfortunately, we get error=7, Argument list too long
        processor.run("{\"partId1\": {\"R00C00\": { \"site1\":{\"aTB_0\": \"0.0\"}}}}", "/Users/jli8/Downloads");

        // Using method 2
        // processor.run("'/Users/jli8/activedir/200-phdf/resources/testfilewriter-2047225563688979.txt'", "'/Users/jli8/Downloads'");
        processor.run("/Users/jli8/activedir/200-phdf/resources/testfilewriter-2047225563688979.txt", "/Users/jli8/Downloads");
    }

}
