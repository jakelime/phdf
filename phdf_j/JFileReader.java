package phdf_j;

// Reading data from a file using FileReader

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;

public class JFileReader {

    public String filepath;

    public JFileReader(String input_filepath) {
        this.filepath = input_filepath;
        System.out.println("intiailised filepath = " + filepath);
    }

    public String read() {
        String everything = "";
        BufferedReader br;
        try {
            br = new BufferedReader(new FileReader(this.filepath));
            try {
                StringBuilder sb = new StringBuilder();
                String line = br.readLine();

                while (line != null) {
                    sb.append(line);
                    sb.append(System.lineSeparator());
                    line = br.readLine();
                }
                everything = sb.toString();
            } finally {
                br.close();
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        return everything;
    }

}
