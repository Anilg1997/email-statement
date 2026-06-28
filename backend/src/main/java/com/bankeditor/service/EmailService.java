package com.bankeditor.service;

import jakarta.mail.internet.InternetAddress;
import jakarta.mail.internet.MimeMessage;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.mail.javamail.JavaMailSenderImpl;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Properties;

@Service
public class EmailService {

    private volatile JavaMailSenderImpl mailSender;
    private volatile EmailConfig currentConfig;

    public static class EmailConfig {
        public String host;
        public int port;
        public String username;
        public String password;
        public boolean useSsl;
        public String fromName;

        public boolean isConfigured() {
            return host != null && !host.isEmpty()
                && username != null && !username.isEmpty()
                && password != null && !password.isEmpty();
        }
    }

    public boolean isConfigured() {
        return currentConfig != null && currentConfig.isConfigured();
    }

    public Map<String, Object> getConfigStatus() {
        Map<String, Object> status = new LinkedHashMap<>();
        status.put("configured", isConfigured());
        if (currentConfig != null) {
            status.put("host", currentConfig.host != null ? currentConfig.host : "");
            status.put("port", currentConfig.port);
            status.put("username", currentConfig.username != null ? currentConfig.username : "");
            status.put("fromName", currentConfig.fromName != null ? currentConfig.fromName : "Bank Statement Service");
        }
        return status;
    }

    public void configure(EmailConfig config) {
        this.currentConfig = config;
        JavaMailSenderImpl impl = new JavaMailSenderImpl();
        impl.setHost(config.host);
        impl.setPort(config.port);
        impl.setUsername(config.username);
        impl.setPassword(config.password);

        Properties props = new Properties();
        props.put("mail.smtp.auth", "true");
        if (config.port == 465) {
            // Port 465 uses direct SSL
            props.put("mail.smtp.ssl.enable", "true");
        } else {
            // Port 587 uses STARTTLS (upgrade from plain to encrypted)
            props.put("mail.smtp.starttls.enable", "true");
            props.put("mail.smtp.starttls.required", "true");
        }
        props.put("mail.smtp.connectiontimeout", "10000");
        props.put("mail.smtp.timeout", "10000");
        props.put("mail.debug", "false");
        impl.setJavaMailProperties(props);

        this.mailSender = impl;
    }

    public Map<String, Object> sendStatementEmail(String toEmail, String bankName, String accountHolder,
                                                   String accountId, byte[] pdfBytes, String password) {
        Map<String, Object> result = new LinkedHashMap<>();

        if (!isConfigured()) {
            result.put("status", "error");
            result.put("message", "Email is not configured. Please set SMTP settings first.");
            return result;
        }
        if (mailSender == null) {
            result.put("status", "error");
            result.put("message", "Mail sender not initialized. Configure email first.");
            return result;
        }

        try {
            MimeMessage message = mailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(message, true);

            String maskedAccount = maskAccount(accountId);
            String fromAddress = currentConfig.username;
            String fromName = (currentConfig.fromName != null && !currentConfig.fromName.isEmpty())
                ? currentConfig.fromName : "Bank Statement Service";

            try {
                helper.setFrom(new InternetAddress(fromAddress, fromName, "UTF-8"));
            } catch (Exception e) {
                helper.setFrom(fromAddress);
            }
            helper.setTo(toEmail);
            helper.setSubject("Your " + bankName + " Account Statement - " + maskedAccount);

            String htmlBody = "<!DOCTYPE html>" +
                "<html><body style='font-family:Arial,sans-serif;padding:20px;'>" +
                "<div style='max-width:600px;margin:0 auto;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden;'>" +
                "<div style='background:linear-gradient(135deg,#0a1628,#1a1a3e);padding:24px;text-align:center;'>" +
                "<h2 style='color:#fff;margin:0;'>" + bankName + "</h2>" +
                "<p style='color:#8899bb;font-size:13px;margin:4px 0 0 0;'>Secure Statement Delivery</p>" +
                "</div>" +
                "<div style='padding:24px;'>" +
                "<p style='font-size:15px;color:#333;'>Dear <strong>" + accountHolder + "</strong>,</p>" +
                "<p style='font-size:14px;color:#555;line-height:1.6;'>Please find attached your account statement for <strong>" + bankName + "</strong> (Account: " + maskedAccount + ").</p>" +
                "<div style='background:#f0f7ff;border:1px solid #cce5ff;border-radius:8px;padding:16px;margin:20px 0;'>" +
                "<p style='font-size:13px;color:#555;margin:0 0 8px 0;'><strong>Statement Details:</strong></p>" +
                "<table width='100%' cellpadding='4' cellspacing='0' style='font-size:13px;color:#555;'>" +
                "<tr><td style='color:#999;width:120px;'>Account Holder:</td><td style='font-weight:600;'>" + accountHolder + "</td></tr>" +
                "<tr><td style='color:#999;'>Account Number:</td><td style='font-weight:600;'>" + maskedAccount + "</td></tr>" +
                "<tr><td style='color:#999;'>PDF Password:</td><td style='font-weight:600;color:#2563eb;'>" + password + "</td></tr>" +
                "</table></div>" +
                "<p style='font-size:13px;color:#666;line-height:1.5;'>The statement PDF is password-protected. Use the last 4 digits of your account number (<strong>" + password + "</strong>) to open it.</p>" +
                "<p style='font-size:13px;color:#999;line-height:1.5;margin:20px 0 0 0;'>This is an automated message from " + bankName + ". Please do not reply to this email.</p>" +
                "</div>" +
                "<div style='background:#f8f9fb;padding:16px;text-align:center;border-top:1px solid #e0e0e0;'>" +
                "<p style='font-size:12px;color:#999;margin:0;'>&copy; 2024 " + bankName + ". All rights reserved.</p>" +
                "</div>" +
                "</div></body></html>";

            helper.setText(htmlBody, true);

            String filename = "statement-" + accountId + ".pdf";
            helper.addAttachment(filename, new ByteArrayResource(pdfBytes));

            mailSender.send(message);
            result.put("status", "ok");
            result.put("message", "Email sent successfully to " + toEmail);
            result.put("to", toEmail);
            result.put("subject", message.getSubject());
            result.put("attachment", filename);
        } catch (Exception e) {
            result.put("status", "error");
            result.put("message", "Failed to send email: " + e.getMessage());
        }
        return result;
    }

    private String maskAccount(String accountId) {
        if (accountId == null || accountId.length() < 4) return accountId;
        String lastFour = accountId.substring(accountId.length() - 4);
        String masked = "X".repeat(Math.max(0, accountId.length() - 4));
        return masked + lastFour;
    }
}
