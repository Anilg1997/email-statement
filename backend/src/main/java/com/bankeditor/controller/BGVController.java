package com.bankeditor.controller;

import com.bankeditor.service.PdfGenerationService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/bgv")
public class BGVController {

    private final PdfGenerationService pdfGenerationService;
    private final Map<String, VerificationLink> verificationLinks = new ConcurrentHashMap<>();
    private final Map<String, Map<String, Object>> savedStatements;

    public BGVController(PdfGenerationService pdfGenerationService) {
        this.pdfGenerationService = pdfGenerationService;
        this.savedStatements = new ConcurrentHashMap<>();
    }

    /**
     * Store a snapshot of statement data for BGV verification
     */
    @PostMapping("/store-statement")
    public ResponseEntity<Map<String, String>> storeStatement(@RequestBody Map<String, Object> data) {
        try {
            String accountNumber = (String) data.getOrDefault("accountNumber", "0000");
            String token = UUID.randomUUID().toString().substring(0, 8).toUpperCase();
            savedStatements.put(token, new HashMap<>(data));
            savedStatements.put(accountNumber, new HashMap<>(data));

            Map<String, String> response = new HashMap<>();
            response.put("status", "ok");
            response.put("token", token);
            response.put("message", "Statement stored for verification");
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of("status", "error", "message", e.getMessage()));
        }
    }

    /**
     * Generate a BGV verification link for an account
     */
    @PostMapping("/generate-link")
    public ResponseEntity<Map<String, Object>> generateLink(@RequestBody Map<String, String> request) {
        try {
            String accountId = request.get("accountId");
            String mode = request.getOrDefault("mode", "portal"); // portal, pdf, email
            String bankName = request.getOrDefault("bankName", "Your Bank");
            String accountHolder = request.getOrDefault("accountHolder", "Account Holder");

            if (accountId == null || accountId.isBlank()) {
                return ResponseEntity.badRequest().body(Map.of("status", "error", "message", "accountId required"));
            }

            String token = UUID.randomUUID().toString().replace("-", "").substring(0, 16).toUpperCase();
            String verificationId = "BGV-" + token;

            VerificationLink link = new VerificationLink();
            link.verificationId = verificationId;
            link.accountId = accountId;
            link.bankName = bankName;
            link.accountHolder = accountHolder;
            link.mode = mode;
            link.createdAt = LocalDateTime.now();
            link.status = "active";
            link.accessCount = 0;

            verificationLinks.put(verificationId, link);

            String baseUrl = getBaseUrl(request);
            String viewUrl = baseUrl + "/api/bgv/view/" + verificationId;

            Map<String, Object> response = new LinkedHashMap<>();
            response.put("status", "ok");
            response.put("verificationId", verificationId);
            response.put("token", token);
            response.put("viewUrl", viewUrl);
            response.put("createdAt", link.createdAt.toString());
            response.put("password", accountId.length() >= 4 ? accountId.substring(accountId.length() - 4) : accountId);
            response.put("mode", mode);

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of("status", "error", "message", e.getMessage()));
        }
    }

    /**
     * Serve the bank portal viewer page for a verification link
     */
    @GetMapping(value = "/view/{verificationId}", produces = MediaType.TEXT_HTML_VALUE)
    public ResponseEntity<String> viewStatement(@PathVariable String verificationId,
                                                  HttpServletRequest request) {
        VerificationLink link = verificationLinks.get(verificationId);
        if (link == null) {
            String errorPage = "<!DOCTYPE html><html><head><title>Invalid Link</title><style>" +
                "body{font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;background:#f5f5f5;}" +
                ".card{text-align:center;padding:40px;background:#fff;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,0.1);}" +
                "h1{color:#dc2626;}p{color:#666;}</style></head><body>" +
                "<div class='card'><h1>Invalid Verification Link</h1>" +
                "<p>This verification link is invalid or has expired.</p>" +
                "<p>Please contact support for a new verification link.</p></div></body></html>";
            return ResponseEntity.badRequest().body(errorPage);
        }

        link.accessCount++;
        link.lastAccessedAt = LocalDateTime.now();

        // Get statement data
        Map<String, Object> data = savedStatements.get(link.accountId);
        if (data == null) {
            data = createDefaultData(link.accountId, link.bankName, link.accountHolder);
        }

        String html = generateBankPortalPage(link, data);
        return ResponseEntity.ok().body(html);
    }

    /**
     * Generate HTML email template for BGV email confirmation
     */
    @PostMapping("/email-template")
    public ResponseEntity<Map<String, Object>> generateEmailTemplate(@RequestBody Map<String, String> request) {
        try {
            String accountId = request.get("accountId");
            String bankName = request.getOrDefault("bankName", "Your Bank");
            String accountHolder = request.getOrDefault("accountHolder", "Account Holder");
            String toEmail = request.getOrDefault("toEmail", "bgv@verification.com");
            String verificationId = request.getOrDefault("verificationId", "");

            String baseUrl = getBaseUrl(request);
            String viewUrl = baseUrl + "/api/bgv/view/" + verificationId;
            String password = accountId.length() >= 4 ? accountId.substring(accountId.length() - 4) : accountId;

            String emailHtml = generateEmailHtml(bankName, accountHolder, accountId, viewUrl, password, toEmail);
            String emailText = generateEmailText(bankName, accountHolder, accountId, viewUrl, password);

            Map<String, Object> response = new LinkedHashMap<>();
            response.put("status", "ok");
            response.put("subject", "Your " + bankName + " Account Statement - Verification Required");
            response.put("toEmail", toEmail);
            response.put("htmlContent", emailHtml);
            response.put("textContent", emailText);
            response.put("fromEmail", "noreply@" + bankName.toLowerCase().replaceAll("[^a-z0-9]", "") + ".com");
            response.put("attachments", List.of(
                Map.of("type", "statement.pdf", "password", password, "note", "Password-protected PDF attached")
            ));

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of("status", "error", "message", e.getMessage()));
        }
    }

    /**
     * List all verification links
     */
    @GetMapping("/links")
    public ResponseEntity<List<Map<String, Object>>> listLinks() {
        List<Map<String, Object>> result = verificationLinks.values().stream()
            .sorted((a, b) -> b.createdAt.compareTo(a.createdAt))
            .map(link -> {
                Map<String, Object> item = new LinkedHashMap<>();
                item.put("verificationId", link.verificationId);
                item.put("accountId", link.accountId);
                item.put("bankName", link.bankName);
                item.put("accountHolder", link.accountHolder);
                item.put("status", link.status);
                item.put("accessCount", link.accessCount);
                item.put("createdAt", link.createdAt.format(DateTimeFormatter.ISO_LOCAL_DATE_TIME));
                item.put("lastAccessedAt", link.lastAccessedAt != null ?
                    link.lastAccessedAt.format(DateTimeFormatter.ISO_LOCAL_DATE_TIME) : "-");
                String baseUrl = "http://localhost:8080";
                item.put("viewUrl", baseUrl + "/api/bgv/view/" + link.verificationId);
                item.put("password", link.accountId.length() >= 4 ?
                    link.accountId.substring(link.accountId.length() - 4) : link.accountId);
                return item;
            })
            .collect(Collectors.toList());

        return ResponseEntity.ok(result);
    }

    /**
     * Get BGV dashboard stats
     */
    @GetMapping("/stats")
    public ResponseEntity<Map<String, Object>> getStats() {
        long totalLinks = verificationLinks.size();
        long activeLinks = verificationLinks.values().stream().filter(l -> "active".equals(l.status)).count();
        long totalAccesses = verificationLinks.values().stream().mapToInt(l -> l.accessCount).sum();

        Map<String, Object> stats = new LinkedHashMap<>();
        stats.put("totalLinks", totalLinks);
        stats.put("activeLinks", activeLinks);
        stats.put("totalAccesses", totalAccesses);
        return ResponseEntity.ok(stats);
    }

    // ========== Private Helpers ==========

    private String getBaseUrl(Map<String, String> request) {
        return "http://localhost:8080";
    }

    private String getBaseUrl(HttpServletRequest request) {
        return "http://localhost:8080";
    }

    private Map<String, Object> createDefaultData(String accountId, String bankName, String accountHolder) {
        Map<String, Object> data = new HashMap<>();
        data.put("bankName", bankName);
        data.put("accountNumber", accountId);
        data.put("accountHolder", accountHolder);
        data.put("period", "Monthly Statement");
        data.put("branch", "Main Branch");
        data.put("ifsc", "BANK0001234");
        data.put("address", "Customer Address");
        data.put("openingBalance", "25000.00");
        data.put("totalDebits", "0.00");
        data.put("totalCredits", "0.00");
        data.put("closingBalance", "25000.00");

        List<Map<String, String>> txns = new ArrayList<>();
        Map<String, String> txn = new HashMap<>();
        txn.put("date", LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE));
        txn.put("description", "Opening Balance");
        txn.put("debit", "");
        txn.put("credit", "25000.00");
        txns.add(txn);

        data.put("transactions", txns);
        return data;
    }

    /**
     * Generate a realistic bank portal HTML page for the verification view
     */
    private String generateBankPortalPage(VerificationLink link, Map<String, Object> data) {
        String bankName = (String) data.getOrDefault("bankName", "Your Bank");
        String accountHolder = (String) data.getOrDefault("accountHolder", "Account Holder");
        String accountNumber = (String) data.getOrDefault("accountNumber", "XXXXXX0000");
        String maskedAccount = maskAccountNumber(accountNumber);
        String period = (String) data.getOrDefault("period", "Monthly Statement");
        String branch = (String) data.getOrDefault("branch", "Main Branch");
        String ifsc = (String) data.getOrDefault("ifsc", "BANK0001234");
        String address = (String) data.getOrDefault("address", "Customer Address");
        String openingBalance = (String) data.getOrDefault("openingBalance", "0.00");
        String closingBalance = (String) data.getOrDefault("closingBalance", "0.00");
        String totalDebits = (String) data.getOrDefault("totalDebits", "0.00");
        String totalCredits = (String) data.getOrDefault("totalCredits", "0.00");

        @SuppressWarnings("unchecked")
        List<Map<String, String>> transactions = (List<Map<String, String>>) data.getOrDefault("transactions", List.of());

        String currentDate = LocalDateTime.now().format(DateTimeFormatter.ofPattern("dd MMM yyyy, hh:mm a"));
        String visitId = link.verificationId;

        // Build transaction rows
        StringBuilder txnRows = new StringBuilder();
        if (transactions.isEmpty()) {
            txnRows.append("<tr><td colspan='4' style='text-align:center;padding:20px;color:#999;'>No transactions found</td></tr>");
        } else {
            for (int i = 0; i < transactions.size(); i++) {
                Map<String, String> txn = transactions.get(i);
                String bg = (i % 2 == 0) ? "#f8f9fb" : "#ffffff";
                String date = txn.getOrDefault("date", "-");
                String desc = txn.getOrDefault("description", "-");
                String debit = txn.getOrDefault("debit", "");
                String credit = txn.getOrDefault("credit", "");
                String debitStyle = !debit.isEmpty() ? "#dc2626" : "#999";
                String creditStyle = !credit.isEmpty() ? "#16a34a" : "#999";

                txnRows.append("<tr style='background:").append(bg).append(";'>")
                    .append("<td style='padding:10px 12px;border-bottom:1px solid #eee;font-size:13px;color:#555;'>").append(escapeHtml(date)).append("</td>")
                    .append("<td style='padding:10px 12px;border-bottom:1px solid #eee;font-size:13px;color:#333;'>").append(escapeHtml(desc)).append("</td>")
                    .append("<td style='padding:10px 12px;border-bottom:1px solid #eee;font-size:13px;text-align:right;color:").append(debitStyle).append(";'>")
                    .append(!debit.isEmpty() ? "<span style='background:#fef2f2;padding:2px 8px;border-radius:4px;'>\u20B9 " + escapeHtml(debit) + "</span>" : "-").append("</td>")
                    .append("<td style='padding:10px 12px;border-bottom:1px solid #eee;font-size:13px;text-align:right;color:").append(creditStyle).append(";'>")
                    .append(!credit.isEmpty() ? "<span style='background:#f0fdf4;padding:2px 8px;border-radius:4px;'>\u20B9 " + escapeHtml(credit) + "</span>" : "-").append("</td>")
                    .append("</tr>");
            }
        }

        String password = link.accountId.length() >= 4 ? link.accountId.substring(link.accountId.length() - 4) : link.accountId;

        return "<!DOCTYPE html>" +
        "<html lang='en'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'>" +
        "<title>" + escapeHtml(bankName) + " - Account Statement</title>" +
        "<style>" +
            "*{margin:0;padding:0;box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;}" +
            "body{background:#f0f2f5;color:#333;}" +
            ".top-bar{background:linear-gradient(135deg,#0a1628 0%,#1a1a3e 100%);color:#fff;padding:0 40px;height:64px;display:flex;align-items:center;justify-content:space-between;}" +
            ".top-bar .bank-logo{display:flex;align-items:center;gap:12px;}" +
            ".top-bar .bank-logo .logo-icon{width:40px;height:40px;background:linear-gradient(135deg,#4a9eff,#2563eb);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:bold;}" +
            ".top-bar .bank-name{font-size:20px;font-weight:700;}" +
            ".top-bar .bank-tagline{font-size:11px;color:#8899bb;}" +
            ".top-bar .secure-badge{display:flex;align-items:center;gap:8px;background:rgba(255,255,255,0.1);padding:8px 16px;border-radius:8px;font-size:12px;color:#aabbdd;}" +
            ".nav-bar{background:#fff;border-bottom:1px solid #e0e0e0;padding:0 40px;display:flex;gap:0;}" +
            ".nav-bar .nav-item{padding:14px 24px;font-size:13px;font-weight:600;color:#666;border-bottom:3px solid transparent;cursor:default;}" +
            ".nav-bar .nav-item.active{color:#2563eb;border-bottom-color:#2563eb;}" +
            ".nav-bar .nav-item:hover{color:#2563eb;}" +
            ".container{max-width:1100px;margin:24px auto;padding:0 20px;}" +
            ".welcome-bar{background:linear-gradient(135deg,#2563eb,#1d4ed8);border-radius:12px;padding:24px 32px;color:#fff;margin-bottom:24px;display:flex;justify-content:space-between;align-items:center;}" +
            ".welcome-bar h1{font-size:22px;font-weight:700;}" +
            ".welcome-bar p{font-size:13px;opacity:0.9;margin-top:4px;}" +
            ".welcome-bar .visit-info{text-align:right;font-size:12px;opacity:0.8;}" +
            ".card{background:#fff;border-radius:12px;box-shadow:0 1px 4px rgba(0,0,0,0.06);margin-bottom:20px;overflow:hidden;}" +
            ".card-header{padding:16px 24px;border-bottom:1px solid #f0f0f0;display:flex;align-items:center;justify-content:space-between;}" +
            ".card-header h2{font-size:16px;font-weight:600;color:#1a1a2e;}" +
            ".card-header .badge{font-size:11px;color:#999;}" +
            ".card-body{padding:20px 24px;}" +
            ".info-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;}" +
            ".info-item .label{font-size:11px;color:#999;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;}" +
            ".info-item .value{font-size:15px;color:#333;font-weight:500;}" +
            "table{width:100%;border-collapse:collapse;}" +
            "th{padding:12px 12px;font-size:11px;font-weight:600;color:#666;text-align:left;border-bottom:2px solid #e0e0e0;text-transform:uppercase;letter-spacing:0.5px;}" +
            ".summary-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;}" +
            ".summary-item{padding:20px;border-radius:10px;text-align:center;}" +
            ".summary-item .amount{font-size:24px;font-weight:700;margin-top:4px;}" +
            ".summary-item .label{font-size:12px;opacity:0.8;}" +
            ".summary-item.opening{background:#f0f7ff;color:#2563eb;}" +
            ".summary-item.debits{background:#fef2f2;color:#dc2626;}" +
            ".summary-item.credits{background:#f0fdf4;color:#16a34a;}" +
            ".summary-item.closing{background:#f5f3ff;color:#7c3aed;}" +
            ".footer-bar{background:#0a1628;color:#8899bb;padding:20px 40px;text-align:center;font-size:12px;}" +
            ".footer-bar a{color:#4a9eff;text-decoration:none;}" +
            ".verify-banner{background:#fefce8;border:1px solid #fde68a;border-radius:8px;padding:12px 16px;margin-bottom:20px;display:flex;align-items:center;gap:12px;font-size:13px;color:#92400e;}" +
            ".verify-banner strong{color:#78350f;}" +
            "@media(max-width:768px){.summary-grid{grid-template-columns:1fr 1fr;}.info-grid{grid-template-columns:1fr;}.top-bar{padding:0 16px;}.nav-bar{padding:0 16px;overflow-x:auto;}}" +
        "</style></head><body>" +

        // Top Bar
        "<div class='top-bar'>" +
            "<div class='bank-logo'>" +
                "<div class='logo-icon'>" + escapeHtml(bankName.substring(0,1)) + "</div>" +
                "<div><div class='bank-name'>" + escapeHtml(bankName) + "</div><div class='bank-tagline'>NetBanking Portal</div></div>" +
            "</div>" +
            "<div class='secure-badge'>\uD83D\uDD12 SECURE | " + escapeHtml(currentDate) + "</div>" +
        "</div>" +

        // Nav Bar
        "<div class='nav-bar'>" +
            "<div class='nav-item active'>Account Summary</div>" +
            "<div class='nav-item'>Statements</div>" +
            "<div class='nav-item'>Transactions</div>" +
            "<div class='nav-item'>Downloads</div>" +
            "<div class='nav-item'>Settings</div>" +
        "</div>" +

        // Container
        "<div class='container'>" +

            // Verification banner
            "<div class='verify-banner'>" +
                "\u2705 <div><strong>Verified Statement</strong> &mdash; This is an official bank statement generated for verification purpose (ID: " + escapeHtml(visitId) + "). " +
                "Password to open attached PDF: <strong>" + escapeHtml(password) + "</strong></div>" +
            "</div>" +

            // Welcome bar
            "<div class='welcome-bar'>" +
                "<div>" +
                    "<h1>Welcome, " + escapeHtml(accountHolder) + "</h1>" +
                    "<p>" + escapeHtml(bankName) + " | Account: " + escapeHtml(maskedAccount) + "</p>" +
                "</div>" +
                "<div class='visit-info'>" +
                    "<div>Visit ID: " + escapeHtml(visitId) + "</div>" +
                    "<div>Generated: " + escapeHtml(currentDate) + "</div>" +
                "</div>" +
            "</div>" +

            // Account Info Card
            "<div class='card'>" +
                "<div class='card-header'><h2>Account Information</h2><span class='badge'>" + escapeHtml(period) + "</span></div>" +
                "<div class='card-body'>" +
                    "<div class='info-grid'>" +
                        "<div class='info-item'><div class='label'>Account Holder</div><div class='value'>" + escapeHtml(accountHolder) + "</div></div>" +
                        "<div class='info-item'><div class='label'>Account Number</div><div class='value'>" + escapeHtml(maskedAccount) + "</div></div>" +
                        "<div class='info-item'><div class='label'>Branch</div><div class='value'>" + escapeHtml(branch) + "</div></div>" +
                        "<div class='info-item'><div class='label'>IFSC Code</div><div class='value'>" + escapeHtml(ifsc) + "</div></div>" +
                        "<div class='info-item'><div class='label'>Address</div><div class='value'>" + escapeHtml(address) + "</div></div>" +
                        "<div class='info-item'><div class='label'>Statement Period</div><div class='value'>" + escapeHtml(period) + "</div></div>" +
                    "</div>" +
                "</div>" +
            "</div>" +

            // Summary Cards
            "<div class='summary-grid'>" +
                "<div class='summary-item opening'><div class='label'>Opening Balance</div><div class='amount'>\u20B9 " + escapeHtml(openingBalance) + "</div></div>" +
                "<div class='summary-item debits'><div class='label'>Total Debits</div><div class='amount'>\u20B9 " + escapeHtml(totalDebits) + "</div></div>" +
                "<div class='summary-item credits'><div class='label'>Total Credits</div><div class='amount'>\u20B9 " + escapeHtml(totalCredits) + "</div></div>" +
                "<div class='summary-item closing'><div class='label'>Closing Balance</div><div class='amount'>\u20B9 " + escapeHtml(closingBalance) + "</div></div>" +
            "</div>" +

            // Transactions Card
            "<div class='card' style='margin-top:20px;'>" +
                "<div class='card-header'><h2>Transaction History</h2><span class='badge'>" + transactions.size() + " entries</span></div>" +
                "<div class='card-body p-0'>" +
                    "<table>" +
                        "<thead><tr>" +
                            "<th style='padding:12px 12px;'>Date</th>" +
                            "<th style='padding:12px 12px;'>Description</th>" +
                            "<th style='padding:12px 12px;text-align:right;'>Debit (\u20B9)</th>" +
                            "<th style='padding:12px 12px;text-align:right;'>Credit (\u20B9)</th>" +
                        "</tr></thead>" +
                        "<tbody>" + txnRows.toString() + "</tbody>" +
                    "</table>" +
                "</div>" +
            "</div>" +

            // PDF Download Section
            "<div class='card'>" +
                "<div class='card-header'><h2>Download Statement</h2><span class='badge'>Password Protected</span></div>" +
                "<div class='card-body' style='display:flex;align-items:center;justify-content:space-between;'>" +
                    "<div><strong>Statement PDF</strong><br><span style='font-size:13px;color:#999;'>Password: <code style='background:#f0f0f0;padding:2px 8px;border-radius:4px;font-size:14px;font-weight:bold;'>" + escapeHtml(password) + "</code> (last 4 digits of account)</span></div>" +
                    "<a href='/api/replace?accountId=" + escapeHtml(link.accountId) + "' target='_blank' style='background:#2563eb;color:#fff;padding:10px 24px;border-radius:8px;text-decoration:none;font-weight:600;font-size:14px;'>\u2B07 Download PDF</a>" +
                "</div>" +
            "</div>" +

        "</div>" +

        // Footer
        "<div class='footer-bar'>" +
            "<p>" + escapeHtml(bankName) + " NetBanking | \u00A9 " + java.time.Year.now().getValue() + " All Rights Reserved</p>" +
            "<p style='margin-top:4px;'>This is a digitally generated statement for verification purposes | Support: support@" + escapeHtml(bankName.toLowerCase().replaceAll("[^a-z0-9]", "")) + ".com</p>" +
        "</div>" +

        "</body></html>";
    }

    /**
     * Generate an HTML email that looks like it came from the bank
     */
    private String generateEmailHtml(String bankName, String accountHolder, String accountId,
                                      String viewUrl, String password, String toEmail) {
        String maskedAccount = maskAccountNumber(accountId);
        String currentDate = LocalDateTime.now().format(DateTimeFormatter.ofPattern("dd MMM yyyy"));

        return "<!DOCTYPE html>" +
        "<html><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'></head>" +
        "<body style='margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,\"Segoe UI\",Roboto,sans-serif;'>" +
        "<table width='100%' cellpadding='0' cellspacing='0' style='background:#f5f5f5;padding:20px;'>" +
        "<tr><td align='center'>" +
        "<table width='600' cellpadding='0' cellspacing='0' style='background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);'>" +

        // Header
        "<tr><td style='background:linear-gradient(135deg,#0a1628,#1a1a3e);padding:30px;text-align:center;'>" +
            "<div style='font-size:28px;font-weight:bold;color:#fff;'>" + escapeHtml(bankName) + "</div>" +
            "<div style='font-size:13px;color:#8899bb;margin-top:4px;'>Secure Account Statement</div>" +
        "</td></tr>" +

        // Body
        "<tr><td style='padding:30px;'>" +
            "<p style='font-size:16px;color:#333;margin:0 0 20px 0;'>Dear <strong>" + escapeHtml(accountHolder) + "</strong>,</p>" +
            "<p style='font-size:14px;color:#555;line-height:1.6;margin:0 0 16px 0;'>" +
                "As requested, please find your account statement for <strong>" + escapeHtml(bankName) + "</strong> (Account: " + escapeHtml(maskedAccount) + ").</p>" +

            "<div style='background:#f0f7ff;border:1px solid #cce5ff;border-radius:8px;padding:16px;margin:20px 0;'>" +
                "<p style='font-size:13px;color:#555;margin:0 0 8px 0;'><strong>Statement Details:</strong></p>" +
                "<table width='100%' cellpadding='4' cellspacing='0' style='font-size:13px;color:#555;'>" +
                    "<tr><td style='color:#999;width:120px;'>Account Holder:</td><td style='font-weight:600;'>" + escapeHtml(accountHolder) + "</td></tr>" +
                    "<tr><td style='color:#999;'>Account Number:</td><td style='font-weight:600;'>" + escapeHtml(maskedAccount) + "</td></tr>" +
                    "<tr><td style='color:#999;'>Date Generated:</td><td style='font-weight:600;'>" + escapeHtml(currentDate) + "</td></tr>" +
                    "<tr><td style='color:#999;'>PDF Password:</td><td style='font-weight:600;color:#2563eb;'>" + escapeHtml(password) + "</td></tr>" +
                "</table>" +
            "</div>" +

            "<p style='font-size:13px;color:#666;line-height:1.5;margin:16px 0;'>" +
                "The statement PDF is password-protected. Use the last 4 digits of your account number (<strong>" + escapeHtml(password) + "</strong>) to open it.</p>" +

            // CTA Button
            "<table cellpadding='0' cellspacing='0' style='margin:24px 0;'>" +
                "<tr><td style='background:#2563eb;border-radius:8px;padding:14px 32px;'>" +
                    "<a href='" + escapeHtml(viewUrl) + "' style='color:#fff;text-decoration:none;font-size:15px;font-weight:600;display:inline-block;'>" +
                        "\uD83D\uDCC4 View Statement Online</a>" +
                "</td></tr>" +
            "</table>" +

            "<div style='background:#fefce8;border:1px solid #fde68a;border-radius:8px;padding:12px;margin:16px 0;font-size:13px;color:#92400e;'>" +
                "\u26A0\uFE0F <strong>Important:</strong> If you did not request this statement, please contact us immediately at security@" + escapeHtml(bankName.toLowerCase().replaceAll("[^a-z0-9]", "")) + ".com</div>" +

            "<p style='font-size:13px;color:#999;line-height:1.5;margin:16px 0 0 0;'>" +
                "This is an automated message from " + escapeHtml(bankName) + ". Please do not reply to this email.</p>" +
        "</td></tr>" +

        // Footer
        "<tr><td style='background:#f8f9fb;padding:20px;text-align:center;border-top:1px solid #e0e0e0;'>" +
            "<p style='font-size:12px;color:#999;margin:0;'>\u00A9 " + java.time.Year.now().getValue() + " " + escapeHtml(bankName) + ". All rights reserved.</p>" +
            "<p style='font-size:11px;color:#bbb;margin:4px 0 0 0;'>NetBanking Portal | Secure Document Delivery</p>" +
        "</td></tr>" +

        "</table>" +
        "</td></tr></table>" +
        "</body></html>";
    }

    private String generateEmailText(String bankName, String accountHolder, String accountId,
                                      String viewUrl, String password) {
        return "Dear " + accountHolder + ",\n\n" +
            "As requested, please find your account statement for " + bankName + ".\n\n" +
            "Account: " + maskAccountNumber(accountId) + "\n" +
            "PDF Password: " + password + "\n\n" +
            "View Online: " + viewUrl + "\n\n" +
            "If you did not request this statement, please contact us immediately.\n\n" +
            bankName + " - Secure Document Delivery";
    }

    private String maskAccountNumber(String accountNumber) {
        if (accountNumber == null || accountNumber.length() < 4) return accountNumber;
        int visible = 4;
        String lastFour = accountNumber.substring(accountNumber.length() - visible);
        String masked = "X".repeat(Math.max(0, accountNumber.length() - visible));
        return masked + lastFour;
    }

    private String escapeHtml(String s) {
        if (s == null) return "";
        return s.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\"", "&quot;")
                .replace("'", "&#39;");
    }

    // ========== Inner Class ==========

    static class VerificationLink {
        String verificationId;
        String accountId;
        String bankName;
        String accountHolder;
        String mode;
        LocalDateTime createdAt;
        LocalDateTime lastAccessedAt;
        String status;
        int accessCount;
    }
}
