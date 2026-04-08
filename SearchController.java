package com.search;

import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import java.io.*;
import java.util.*;

@RestController
@CrossOrigin(origins = "*")
@RequestMapping("/api")
public class SearchController {

    // Update this to the absolute path of search_engine.py on your machine
    private static final String PYTHON_SCRIPT = "../python_engine/search_engine.py";

    @PostMapping("/search")
    public ResponseEntity<String> search(@RequestBody Map<String, Object> body) {
        String query = (String) body.get("query");
        @SuppressWarnings("unchecked")
        List<String> files = (List<String>) body.get("filePaths");

        if (query == null || query.isBlank())
            return ResponseEntity.badRequest().body("{\"error\":\"Query is empty\"}");
        if (files == null || files.isEmpty())
            return ResponseEntity.badRequest().body("{\"error\":\"No files provided\"}");

        try {
            return ResponseEntity.ok(runPython(query, files));
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body("{\"error\":\"" + e.getMessage() + "\"}");
        }
    }

    private String runPython(String query, List<String> files) throws IOException, InterruptedException {
        List<String> cmd = new ArrayList<>(List.of("python3", PYTHON_SCRIPT, query));
        cmd.addAll(files);

        Process process = new ProcessBuilder(cmd).start();

        StringBuilder output = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
            String line;
            while ((line = reader.readLine()) != null) output.append(line).append("\n");
        }

        process.waitFor();
        return output.toString().trim();
    }

    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("{\"status\":\"ok\"}");
    }
}
