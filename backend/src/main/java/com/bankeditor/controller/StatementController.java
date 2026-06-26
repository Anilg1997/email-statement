package com.bankeditor.controller;

import com.bankeditor.service.PdfEncryptionService;
import com.bankeditor.service.PdfGenerationService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import com.itextpdf.text.pdf.PdfReader;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@RestController
@RequestMapping("/api")
public class StatementController {

    private final PdfGenerationService pdfGenerationService;
    private final PdfEncryptionService pdfEncryptionService;
    private final Map<String, Map<String, Object>> savedStatements = new ConcurrentHashMap<>();
    private final Map<String, byte[]> uploadedPdfs = new ConcurrentHashMap<>();
    private final Map<String, String> uploadedMeta = new ConcurrentHashMap<>();

    public StatementController(PdfGenerationService pdfGenerationService,
                               PdfEncryptionService pdfEncryptionService) {
        this.pdfGenerationService = pdfGenerationService;
        this.pdfEncryptionService = pdfEncryptionService;
    }

    @PostMapping("/generate")
    public ResponseEntity<byte[]> generate(@RequestBody Map<String, Object> data) {
        try {
            String accountNumber = (String) data.getOrDefault("accountNumber", "0000");
            savedStatements.put(accountNumber, data);
            byte[] pdfBytes = pdfGenerationService.generateStatement(data);
            String password = accountNumber.substring(Math.max(0, accountNumber.length() - 4));
            byte[] encryptedPdf = pdfEncryptionService.encryptPdf(pdfBytes, password);
            HttpHeaders h = new HttpHeaders();
            h.setContentType(MediaType.APPLICATION_PDF);
            h.setContentDispositionFormData("attachment", "statement.pdf");
            h.setContentLength(encryptedPdf.length);
            return ResponseEntity.ok().headers(h).body(encryptedPdf);
        } catch (Exception e) {
            return ResponseEntity.internalServerError().build();
        }
    }

    @PostMapping("/generate-plain")
    public ResponseEntity<byte[]> generatePlain(@RequestBody Map<String, Object> data) {
        try {
            byte[] pdfBytes = pdfGenerationService.generateStatement(data);
            HttpHeaders h = new HttpHeaders();
            h.setContentType(MediaType.APPLICATION_PDF);
            h.setContentDispositionFormData("attachment", "statement.pdf");
            h.setContentLength(pdfBytes.length);
            return ResponseEntity.ok().headers(h).body(pdfBytes);
        } catch (Exception e) {
            return ResponseEntity.internalServerError().build();
        }
    }

    @PostMapping("/upload")
    public ResponseEntity<Map<String, String>> upload(
            @RequestParam String accountId,
            @RequestParam("file") MultipartFile file) {
        try {
            uploadedPdfs.put(accountId, file.getBytes());
            uploadedMeta.put(accountId, file.getOriginalFilename() + " (" + file.getSize() + " bytes)");
            return ResponseEntity.ok(Map.of("status", "ok", "message",
                    "Uploaded " + file.getOriginalFilename() + " for account " + accountId));
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of("status", "error", "message", e.getMessage()));
        }
    }

    @GetMapping("/list")
    public ResponseEntity<List<Map<String, String>>> list() {
        List<Map<String, String>> result = new ArrayList<>();
        for (String accountId : uploadedPdfs.keySet()) {
            Map<String, String> item = new HashMap<>();
            item.put("accountId", accountId);
            item.put("file", uploadedMeta.getOrDefault(accountId, "PDF uploaded"));
            result.add(item);
        }
        for (String accountId : savedStatements.keySet()) {
            if (!uploadedPdfs.containsKey(accountId)) {
                Map<String, String> item = new HashMap<>();
                item.put("accountId", accountId);
                item.put("file", "Generated via editor");
                result.add(item);
            }
        }
        return ResponseEntity.ok(result);
    }

    @GetMapping("/replace")
    public ResponseEntity<byte[]> replace(HttpServletRequest request) {
        String accountId = request.getParameter("accountId");
        if (accountId == null || accountId.isBlank()) {
            return ResponseEntity.badRequest().build();
        }
        try {
            byte[] pdfBytes;
            if (uploadedPdfs.containsKey(accountId)) {
                pdfBytes = uploadedPdfs.get(accountId);
            } else {
                Map<String, Object> data = savedStatements.get(accountId);
                if (data == null) data = createDefaultData(accountId);
                pdfBytes = pdfGenerationService.generateStatement(data);
            }
            String password = accountId.substring(Math.max(0, accountId.length() - 4));
            byte[] encryptedPdf = pdfEncryptionService.encryptPdf(pdfBytes, password);
            HttpHeaders h = new HttpHeaders();
            h.setContentType(MediaType.APPLICATION_PDF);
            h.setContentDispositionFormData("inline", "statement.pdf");
            h.setContentLength(encryptedPdf.length);
            return ResponseEntity.ok().headers(h).body(encryptedPdf);
        } catch (Exception e) {
            return ResponseEntity.internalServerError().build();
        }
    }

    @PostMapping("/import-pdf")
    public ResponseEntity<Map<String, Object>> importPdf(@RequestParam("file") MultipartFile file) {
        try {
            byte[] pdfBytes = file.getBytes();
            PdfReader reader = new PdfReader(pdfBytes);
            StringBuilder text = new StringBuilder();
            for (int i = 1; i <= reader.getNumberOfPages(); i++) {
                text.append(com.itextpdf.text.pdf.parser.PdfTextExtractor.getTextFromPage(reader, i));
            }
            reader.close();

            String content = text.toString();
            Map<String, Object> result = new LinkedHashMap<>();
            result.put("status", "ok");
            result.put("extractedText", content.substring(0, Math.min(content.length(), 5000)));

            // Try to extract known fields via regex
            String bankName = tryExtract(content, Arrays.asList(
                "(?i)([A-Z]+\\s*BANK)",
                "(?i)(BANK\\s+OF\\s+\\w+)",
                "(?i)(\\w+\\s+BANK\\s*$)"
            ));
            result.put("bankName", bankName != null ? bankName : "Imported Bank");

            String accountNumber = tryExtract(content, Arrays.asList(
                "(?:A/C|ACCOUNT|Account)(?:\\s*No|\\s*Number|\\s*#)?[\\s:.#]+(\\d{9,18})",
                "(\\d{9,18})"
            ));
            result.put("accountNumber", accountNumber != null ? accountNumber : "");

            String holderName = tryExtract(content, Arrays.asList(
                "(?:Account Holder|Account Name|Name|Customer)[\\s:]+([A-Za-z\\s.]+?)(?:\\n|Account|Branch)",
                "([A-Z][a-z]+\\s+[A-Z][a-z]+)"
            ));
            result.put("accountHolder", holderName != null ? holderName.trim() : "Imported Holder");

            // Extract statement period
            String period = tryExtract(content, Arrays.asList(
                "(?:Period|Statement|For the month)[\\s:]+([A-Za-z]+\\s+\\d{4})",
                "([A-Z][a-z]+\\s+\\d{4})"
            ));
            result.put("period", period != null ? period : "Monthly Statement");

            // Extract balance amounts
            String openingBal = tryExtract(content, Arrays.asList(
                "(?:Opening|Open)(?: Balance)?[\\s:]+[\\u20B9Rs.]*(\\d+[\\.,]\\d{2})",
                "(?:Opening|Open)(?: Balance)?[\\s:]*(\\d+[\\.,]\\d{0,2})"
            ));
            result.put("openingBalance", openingBal != null ? openingBal.replace(",", "") : "0.00");

            String closingBal = tryExtract(content, Arrays.asList(
                "(?:Closing|Balance)[\\s:]+[\\u20B9Rs.]*(\\d+[\\.,]\\d{2})",
                "(?:Closing Balance|Balance)[\\s:]*(\\d+[\\.,]\\d{0,2})",
                "BALANCE\\s*[:\\s]+(\\d+[\\.,]\\d{0,2})"
            ));
            result.put("closingBalance", closingBal != null ? closingBal.replace(",", "") : "0.00");

            return ResponseEntity.ok(result);
        } catch (Exception e) {
            return ResponseEntity.ok(Map.of("status", "ok",
                "message", "Could not extract text from this PDF. Try entering data manually."));
        }
    }

    private String tryExtract(String content, List<String> patterns) {
        for (String pattern : patterns) {
            Matcher m = Pattern.compile(pattern).matcher(content);
            if (m.find() && m.groupCount() >= 1) {
                String val = m.group(1);
                if (val != null && !val.isBlank()) return val.trim();
            }
        }
        return null;
    }

    private Map<String, Object> createDefaultData(String accountId) {
        Map<String, Object> data = new HashMap<>();
        data.put("bankName", "YOUR BANK");
        data.put("accountNumber", accountId);
        data.put("accountHolder", "Account Holder");
        data.put("period", "Current Month");
        data.put("branch", "Main Branch");
        data.put("ifsc", "BANK0001234");
        data.put("address", "Customer Address");
        data.put("openingBalance", "10000.00");
        data.put("totalDebits", "0.00");
        data.put("totalCredits", "0.00");
        data.put("closingBalance", "10000.00");
        data.put("transactions", List.of());
        return data;
    }
}
