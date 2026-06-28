package com.bankeditor.service;

import com.itextpdf.text.*;
import com.itextpdf.text.pdf.PdfPCell;
import com.itextpdf.text.pdf.PdfPTable;
import com.itextpdf.text.pdf.PdfWriter;
import com.itextpdf.text.pdf.draw.LineSeparator;
import org.springframework.stereotype.Service;

import java.io.ByteArrayOutputStream;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class PdfGenerationService {

    private static final Font TITLE_FONT = new Font(Font.FontFamily.HELVETICA, 22, Font.BOLD, new BaseColor(0x1a, 0x1a, 0x2e));
    private static final Font SUBTITLE_FONT = new Font(Font.FontFamily.HELVETICA, 12, Font.BOLD, new BaseColor(0x33, 0x33, 0x33));
    private static final Font NORMAL_FONT = new Font(Font.FontFamily.HELVETICA, 10, Font.NORMAL, new BaseColor(0x44, 0x44, 0x44));
    private static final Font LABEL_FONT = new Font(Font.FontFamily.HELVETICA, 10, Font.BOLD, new BaseColor(0x66, 0x66, 0x66));
    private static final Font TOTAL_FONT = new Font(Font.FontFamily.HELVETICA, 10, Font.BOLD, new BaseColor(0x1a, 0x1a, 0x2e));
    private static final Font AMOUNT_FONT = new Font(Font.FontFamily.HELVETICA, 10, Font.NORMAL, new BaseColor(0x44, 0x44, 0x44));
    private static final Font FOOTER_FONT = new Font(Font.FontFamily.HELVETICA, 8, Font.NORMAL, BaseColor.GRAY);
    private static final BaseColor ALT_ROW_BG = new BaseColor(0xf5, 0xf7, 0xfa);

    // Bank template configurations
    private static final Map<String, BankTemplate> BANK_TEMPLATES = new LinkedHashMap<>();
    static {
        // HDFC Bank
        BankTemplate hdfc = new BankTemplate();
        hdfc.headerBg = new BaseColor(0xF15B22); hdfc.headerText = BaseColor.WHITE;
        hdfc.headerSubText = new BaseColor(0xFDE8D8); hdfc.accentColor = new BaseColor(0xF15B22);
        hdfc.summaryBg = new BaseColor(0xFEF3ED); hdfc.tableHeaderBg = new BaseColor(0xF15B22);
        hdfc.statementLabel = "ACCOUNT STATEMENT"; hdfc.barColor = new BaseColor(0xF15B22);
        BANK_TEMPLATES.put("HDFC", hdfc);

        // ICICI Bank
        BankTemplate icici = new BankTemplate();
        icici.headerBg = new BaseColor(0xCC0028); icici.headerText = BaseColor.WHITE;
        icici.headerSubText = new BaseColor(0xF5CCD3); icici.accentColor = new BaseColor(0xCC0028);
        icici.summaryBg = new BaseColor(0xFDE8EB); icici.tableHeaderBg = new BaseColor(0xCC0028);
        icici.statementLabel = "ACCOUNT STATEMENT"; icici.barColor = new BaseColor(0xCC0028);
        BANK_TEMPLATES.put("ICICI", icici);

        // SBI
        BankTemplate sbi = new BankTemplate();
        sbi.headerBg = new BaseColor(0x1A5276); sbi.headerText = BaseColor.WHITE;
        sbi.headerSubText = new BaseColor(0xB8D4E8); sbi.accentColor = new BaseColor(0x1A5276);
        sbi.summaryBg = new BaseColor(0xE8F0F8); sbi.tableHeaderBg = new BaseColor(0x1A5276);
        sbi.statementLabel = "ACCOUNT STATEMENT"; sbi.barColor = new BaseColor(0x1A5276);
        BANK_TEMPLATES.put("SBI", sbi);

        // Axis Bank
        BankTemplate axis = new BankTemplate();
        axis.headerBg = new BaseColor(0x8B1A4A); axis.headerText = BaseColor.WHITE;
        axis.headerSubText = new BaseColor(0xE8C4D4); axis.accentColor = new BaseColor(0x8B1A4A);
        axis.summaryBg = new BaseColor(0xF8EEF2); axis.tableHeaderBg = new BaseColor(0x8B1A4A);
        axis.statementLabel = "ACCOUNT STATEMENT"; axis.barColor = new BaseColor(0x8B1A4A);
        BANK_TEMPLATES.put("Axis", axis);

        // Yes Bank
        BankTemplate yes = new BankTemplate();
        yes.headerBg = new BaseColor(0x003B71); yes.headerText = BaseColor.WHITE;
        yes.headerSubText = new BaseColor(0xB8D0E8); yes.accentColor = new BaseColor(0x003B71);
        yes.summaryBg = new BaseColor(0xE8F0F8); yes.tableHeaderBg = new BaseColor(0x003B71);
        yes.statementLabel = "ACCOUNT STATEMENT"; yes.barColor = new BaseColor(0x003B71);
        BANK_TEMPLATES.put("Yes Bank", yes);

        // Kotak Mahindra
        BankTemplate kotak = new BankTemplate();
        kotak.headerBg = new BaseColor(0x003366); kotak.headerText = BaseColor.WHITE;
        kotak.headerSubText = new BaseColor(0xB8CCE0); kotak.accentColor = new BaseColor(0x003366);
        kotak.summaryBg = new BaseColor(0xE8F0F8); kotak.tableHeaderBg = new BaseColor(0x003366);
        kotak.statementLabel = "ACCOUNT STATEMENT"; kotak.barColor = new BaseColor(0x003366);
        BANK_TEMPLATES.put("Kotak", kotak);

        // Default template (generic dark)
        BankTemplate def = new BankTemplate();
        def.headerBg = new BaseColor(0x1a, 0x1a, 0x2e); def.headerText = BaseColor.WHITE;
        def.headerSubText = new BaseColor(0xcc, 0xcc, 0xdd); def.accentColor = new BaseColor(0x1a, 0x1a, 0x2e);
        def.summaryBg = new BaseColor(0xf0, 0xf2, 0xf5); def.tableHeaderBg = new BaseColor(0x1a, 0x1a, 0x2e);
        def.statementLabel = "MONTHLY ACCOUNT STATEMENT"; def.barColor = new BaseColor(0x1a, 0x1a, 0x2e);
        BANK_TEMPLATES.put("default", def);
    }

    public byte[] generateStatement(Map<String, Object> data) throws Exception {
        String bankName = (String) data.getOrDefault("bankName", "YOUR BANK");
        BankTemplate tmpl = resolveTemplate(bankName);

        Document document = new Document(PageSize.A4, 36, 36, 36, 36);
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        PdfWriter.getInstance(document, baos);
        document.open();

        addHeader(document, data, tmpl);
        addAccountInfo(document, data);
        addTransactionTable(document, data, tmpl);
        addSummary(document, data, tmpl);
        addFooter(document, data, tmpl);

        document.close();
        return baos.toByteArray();
    }

    private BankTemplate resolveTemplate(String bankName) {
        if (bankName == null) return BANK_TEMPLATES.get("default");
        for (Map.Entry<String, BankTemplate> e : BANK_TEMPLATES.entrySet()) {
            if (bankName.toUpperCase().contains(e.getKey().toUpperCase())) {
                return e.getValue();
            }
        }
        return BANK_TEMPLATES.get("default");
    }

    private void addHeader(Document doc, Map<String, Object> data, BankTemplate tmpl) throws DocumentException {
        String bankName = (String) data.getOrDefault("bankName", "YOUR BANK");

        PdfPTable headerTable = new PdfPTable(1);
        headerTable.setWidthPercentage(100);
        headerTable.getDefaultCell().setBorder(Rectangle.NO_BORDER);

        PdfPCell titleCell = new PdfPCell();
        titleCell.setBorder(Rectangle.NO_BORDER);
        titleCell.setBackgroundColor(tmpl.headerBg);
        titleCell.setPadding(20);

        Paragraph bankPara = new Paragraph(bankName.toUpperCase(),
                new Font(Font.FontFamily.HELVETICA, 26, Font.BOLD, tmpl.headerText));
        bankPara.setAlignment(Element.ALIGN_CENTER);
        titleCell.addElement(bankPara);

        Paragraph statementPara = new Paragraph(tmpl.statementLabel,
                new Font(Font.FontFamily.HELVETICA, 11, Font.NORMAL, tmpl.headerSubText));
        statementPara.setAlignment(Element.ALIGN_CENTER);
        titleCell.addElement(statementPara);

        // Add decorative line
        Paragraph deco = new Paragraph("-".repeat(60),
                new Font(Font.FontFamily.HELVETICA, 6, Font.NORMAL, tmpl.headerSubText));
        deco.setAlignment(Element.ALIGN_CENTER);
        titleCell.addElement(deco);

        headerTable.addCell(titleCell);
        doc.add(headerTable);
        doc.add(new Paragraph(" "));
    }

    private void addAccountInfo(Document doc, Map<String, Object> data) throws DocumentException {
        PdfPTable infoTable = new PdfPTable(4);
        infoTable.setWidthPercentage(100);
        infoTable.setWidths(new float[]{1, 2, 1, 2});

        addInfoRow(infoTable, "Account Holder:", (String) data.getOrDefault("accountHolder", "John Doe"));
        addInfoRow(infoTable, "Account No.:", (String) data.getOrDefault("accountNumber", "XXXXXX7890"));
        addInfoRow(infoTable, "Branch:", (String) data.getOrDefault("branch", "Main Branch"));
        addInfoRow(infoTable, "Statement Period:", (String) data.getOrDefault("period", "January 2026"));
        addInfoRow(infoTable, "IFSC Code:", (String) data.getOrDefault("ifsc", "BANK0001234"));
        addInfoRow(infoTable, "Address:", (String) data.getOrDefault("address", "123 Main Street"));

        doc.add(infoTable);
        doc.add(new Paragraph(" "));

        Chunk line = new Chunk(new LineSeparator(0.5f, 100, BaseColor.LIGHT_GRAY, Element.ALIGN_CENTER, -2));
        doc.add(new Paragraph(line));
        doc.add(new Paragraph(" "));
    }

    private void addInfoRow(PdfPTable table, String label, String value) {
        PdfPCell lc = new PdfPCell(new Phrase(label, LABEL_FONT));
        lc.setBorder(Rectangle.NO_BORDER); lc.setPadding(2); lc.setPaddingLeft(5);
        table.addCell(lc);
        PdfPCell vc = new PdfPCell(new Phrase(value == null ? "" : value, NORMAL_FONT));
        vc.setBorder(Rectangle.NO_BORDER); vc.setPadding(2);
        table.addCell(vc);
    }

    @SuppressWarnings("unchecked")
    private void addTransactionTable(Document doc, Map<String, Object> data, BankTemplate tmpl) throws DocumentException {
        Paragraph transTitle = new Paragraph("TRANSACTION HISTORY", SUBTITLE_FONT);
        transTitle.setSpacingAfter(8);
        doc.add(transTitle);

        PdfPTable table = new PdfPTable(4);
        table.setWidthPercentage(100);
        table.setWidths(new float[]{1.2f, 3f, 1.2f, 1.2f});

        Font headerFont = new Font(Font.FontFamily.HELVETICA, 10, Font.BOLD, BaseColor.WHITE);
        String[] headers = {"Date", "Description", "Debit (\u20B9)", "Credit (\u20B9)"};
        for (String h : headers) {
            PdfPCell cell = new PdfPCell(new Phrase(h, headerFont));
            cell.setBackgroundColor(tmpl.tableHeaderBg);
            cell.setPadding(8);
            cell.setHorizontalAlignment(Element.ALIGN_CENTER);
            table.addCell(cell);
        }

        List<Map<String, String>> transactions = (List<Map<String, String>>) data.getOrDefault("transactions", List.of());

        if (transactions.isEmpty()) {
            PdfPCell emptyCell = new PdfPCell(new Phrase("No transactions", NORMAL_FONT));
            emptyCell.setColspan(4); emptyCell.setPadding(10);
            emptyCell.setHorizontalAlignment(Element.ALIGN_CENTER);
            table.addCell(emptyCell);
        } else {
            for (int i = 0; i < transactions.size(); i++) {
                Map<String, String> txn = transactions.get(i);
                BaseColor bg = (i % 2 == 0) ? ALT_ROW_BG : BaseColor.WHITE;
                addCell(table, txn.getOrDefault("date", ""), bg, Element.ALIGN_CENTER);
                addCell(table, txn.getOrDefault("description", ""), bg, Element.ALIGN_LEFT);
                addCell(table, txn.getOrDefault("debit", ""), bg, Element.ALIGN_RIGHT);
                addCell(table, txn.getOrDefault("credit", ""), bg, Element.ALIGN_RIGHT);
            }
        }
        doc.add(table);
        doc.add(new Paragraph(" "));
    }

    private void addCell(PdfPTable table, String text, BaseColor bg, int align) {
        PdfPCell cell = new PdfPCell(new Phrase(text.isEmpty() ? "-" : text, NORMAL_FONT));
        cell.setPadding(6); cell.setBackgroundColor(bg);
        cell.setHorizontalAlignment(align); cell.setBorderColor(BaseColor.LIGHT_GRAY);
        table.addCell(cell);
    }

    private void addSummary(Document doc, Map<String, Object> data, BankTemplate tmpl) throws DocumentException {
        Chunk line = new Chunk(new LineSeparator(0.5f, 100, BaseColor.LIGHT_GRAY, Element.ALIGN_CENTER, -2));
        doc.add(new Paragraph(line));
        doc.add(new Paragraph(" "));

        PdfPTable summary = new PdfPTable(2);
        summary.setWidthPercentage(50);
        summary.setHorizontalAlignment(Element.ALIGN_RIGHT);

        addSummaryRow(summary, "Opening Balance:", (String) data.getOrDefault("openingBalance", "0.00"), false, tmpl.accentColor);
        addSummaryRow(summary, "Total Debits:", (String) data.getOrDefault("totalDebits", "0.00"), false, tmpl.accentColor);
        addSummaryRow(summary, "Total Credits:", (String) data.getOrDefault("totalCredits", "0.00"), false, tmpl.accentColor);
        addSummaryRow(summary, "Closing Balance:", (String) data.getOrDefault("closingBalance", "0.00"), true, tmpl.accentColor);

        doc.add(summary);
    }

    private void addSummaryRow(PdfPTable table, String label, String value, boolean isTotal, BaseColor accentColor) {
        Font lf = isTotal ? new Font(Font.FontFamily.HELVETICA, 10, Font.BOLD, accentColor) : LABEL_FONT;
        Font vf = isTotal ? new Font(Font.FontFamily.HELVETICA, 12, Font.BOLD, accentColor) : AMOUNT_FONT;

        PdfPCell lc = new PdfPCell(new Phrase(label, lf));
        lc.setBorder(Rectangle.NO_BORDER); lc.setPadding(4);
        lc.setHorizontalAlignment(Element.ALIGN_LEFT);
        if (isTotal) lc.setBackgroundColor(new BaseColor(0xe8, 0xea, 0xf0));
        table.addCell(lc);

        PdfPCell vc = new PdfPCell(new Phrase("\u20B9 " + value, vf));
        vc.setBorder(Rectangle.NO_BORDER); vc.setPadding(4);
        vc.setHorizontalAlignment(Element.ALIGN_RIGHT);
        if (isTotal) vc.setBackgroundColor(new BaseColor(0xe8, 0xea, 0xf0));
        table.addCell(vc);
    }

    private void addFooter(Document doc, Map<String, Object> data, BankTemplate tmpl) throws DocumentException {
        doc.add(new Paragraph(" "));
        Chunk line = new Chunk(new LineSeparator(0.5f, 100, BaseColor.LIGHT_GRAY, Element.ALIGN_CENTER, -2));
        doc.add(new Paragraph(line));
        doc.add(new Paragraph(" "));

        String bankName = (String) data.getOrDefault("bankName", "YOUR BANK");
        String shortName = bankName.toUpperCase().replaceAll("[^A-Z0-9]", "");

        Paragraph f1 = new Paragraph(
                "This is a computer-generated statement. No signature is required.", FOOTER_FONT);
        f1.setAlignment(Element.ALIGN_CENTER);
        doc.add(f1);

        Paragraph f2 = new Paragraph(
                "For queries, contact customer service | support@" + shortName.toLowerCase() + ".com", FOOTER_FONT);
        f2.setAlignment(Element.ALIGN_CENTER);
        doc.add(f2);

        Paragraph f3 = new Paragraph("Page 1 of 1", FOOTER_FONT);
        f3.setAlignment(Element.ALIGN_CENTER);
        doc.add(f3);
    }

    // Inner class for bank template config
    static class BankTemplate {
        BaseColor headerBg; BaseColor headerText; BaseColor headerSubText;
        BaseColor accentColor; BaseColor summaryBg; BaseColor tableHeaderBg;
        String statementLabel; BaseColor barColor;
    }
}
