package com.bankeditor.service;

import com.itextpdf.text.*;
import com.itextpdf.text.pdf.PdfPCell;
import com.itextpdf.text.pdf.PdfPTable;
import com.itextpdf.text.pdf.PdfWriter;
import com.itextpdf.text.pdf.draw.LineSeparator;
import org.springframework.stereotype.Service;

import java.io.ByteArrayOutputStream;
import java.util.List;
import java.util.Map;

@Service
public class PdfGenerationService {

    private static final Font TITLE_FONT = new Font(Font.FontFamily.HELVETICA, 22, Font.BOLD, new BaseColor(0x1a, 0x1a, 0x2e));
    private static final Font SUBTITLE_FONT = new Font(Font.FontFamily.HELVETICA, 12, Font.BOLD, new BaseColor(0x33, 0x33, 0x33));
    private static final Font NORMAL_FONT = new Font(Font.FontFamily.HELVETICA, 10, Font.NORMAL, new BaseColor(0x44, 0x44, 0x44));
    private static final Font LABEL_FONT = new Font(Font.FontFamily.HELVETICA, 10, Font.BOLD, new BaseColor(0x66, 0x66, 0x66));
    private static final Font HEADER_FONT = new Font(Font.FontFamily.HELVETICA, 10, Font.BOLD, BaseColor.WHITE);
    private static final Font TOTAL_FONT = new Font(Font.FontFamily.HELVETICA, 10, Font.BOLD, new BaseColor(0x1a, 0x1a, 0x2e));
    private static final Font AMOUNT_FONT = new Font(Font.FontFamily.HELVETICA, 10, Font.NORMAL, new BaseColor(0x44, 0x44, 0x44));

    private static final BaseColor HEADER_BG = new BaseColor(0x1a, 0x1a, 0x2e);
    private static final BaseColor ALT_ROW_BG = new BaseColor(0xf5, 0xf7, 0xfa);

    public byte[] generateStatement(Map<String, Object> data) throws Exception {
        Document document = new Document(PageSize.A4, 36, 36, 36, 36);
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        PdfWriter.getInstance(document, baos);
        document.open();

        addHeader(document, data);
        addAccountInfo(document, data);
        addTransactionTable(document, data);
        addSummary(document, data);
        addFooter(document, data);

        document.close();
        return baos.toByteArray();
    }

    private void addHeader(Document doc, Map<String, Object> data) throws DocumentException {
        PdfPTable headerTable = new PdfPTable(1);
        headerTable.setWidthPercentage(100);
        headerTable.getDefaultCell().setBorder(Rectangle.NO_BORDER);

        PdfPCell titleCell = new PdfPCell();
        titleCell.setBorder(Rectangle.NO_BORDER);
        titleCell.setBackgroundColor(HEADER_BG);
        titleCell.setPadding(20);

        Paragraph bankName = new Paragraph(
                (String) data.getOrDefault("bankName", "YOUR BANK"),
                new Font(Font.FontFamily.HELVETICA, 28, Font.BOLD, BaseColor.WHITE)
        );
        bankName.setAlignment(Element.ALIGN_CENTER);
        titleCell.addElement(bankName);

        Paragraph statementType = new Paragraph(
                "MONTHLY ACCOUNT STATEMENT",
                new Font(Font.FontFamily.HELVETICA, 12, Font.NORMAL, new BaseColor(0xcc, 0xcc, 0xdd))
        );
        statementType.setAlignment(Element.ALIGN_CENTER);
        titleCell.addElement(statementType);

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

        Paragraph line = new Paragraph(new Chunk(new LineSeparator(0.5f, 100, BaseColor.LIGHT_GRAY, Element.ALIGN_CENTER, -2)));
        doc.add(line);
        doc.add(new Paragraph(" "));
    }

    private void addInfoRow(PdfPTable table, String label, String value) {
        PdfPCell labelCell = new PdfPCell(new Phrase(label, LABEL_FONT));
        labelCell.setBorder(Rectangle.NO_BORDER);
        labelCell.setPadding(2);
        labelCell.setPaddingLeft(5);
        table.addCell(labelCell);

        PdfPCell valueCell = new PdfPCell(new Phrase(value, NORMAL_FONT));
        valueCell.setBorder(Rectangle.NO_BORDER);
        valueCell.setPadding(2);
        table.addCell(valueCell);
    }

    @SuppressWarnings("unchecked")
    private void addTransactionTable(Document doc, Map<String, Object> data) throws DocumentException {
        Paragraph transTitle = new Paragraph("TRANSACTION HISTORY", SUBTITLE_FONT);
        transTitle.setSpacingAfter(8);
        doc.add(transTitle);

        PdfPTable table = new PdfPTable(4);
        table.setWidthPercentage(100);
        table.setWidths(new float[]{1.2f, 3f, 1.2f, 1.2f});

        String[] headers = {"Date", "Description", "Debit (\u20B9)", "Credit (\u20B9)"};
        for (String h : headers) {
            PdfPCell cell = new PdfPCell(new Phrase(h, HEADER_FONT));
            cell.setBackgroundColor(HEADER_BG);
            cell.setPadding(8);
            cell.setHorizontalAlignment(Element.ALIGN_CENTER);
            table.addCell(cell);
        }

        List<Map<String, String>> transactions = (List<Map<String, String>>) data.getOrDefault("transactions", List.of());

        if (transactions.isEmpty()) {
            PdfPCell emptyCell = new PdfPCell(new Phrase("No transactions", NORMAL_FONT));
            emptyCell.setColspan(4);
            emptyCell.setPadding(10);
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
        cell.setPadding(6);
        cell.setBackgroundColor(bg);
        cell.setHorizontalAlignment(align);
        cell.setBorderColor(BaseColor.LIGHT_GRAY);
        table.addCell(cell);
    }

    private void addSummary(Document doc, Map<String, Object> data) throws DocumentException {
        Paragraph line = new Paragraph(new Chunk(new LineSeparator(0.5f, 100, BaseColor.LIGHT_GRAY, Element.ALIGN_CENTER, -2)));
        doc.add(line);
        doc.add(new Paragraph(" "));

        PdfPTable summary = new PdfPTable(2);
        summary.setWidthPercentage(50);
        summary.setHorizontalAlignment(Element.ALIGN_RIGHT);

        addSummaryRow(summary, "Opening Balance:", (String) data.getOrDefault("openingBalance", "0.00"), false);
        addSummaryRow(summary, "Total Debits:", (String) data.getOrDefault("totalDebits", "0.00"), false);
        addSummaryRow(summary, "Total Credits:", (String) data.getOrDefault("totalCredits", "0.00"), false);
        addSummaryRow(summary, "Closing Balance:", (String) data.getOrDefault("closingBalance", "0.00"), true);

        doc.add(summary);
    }

    private void addSummaryRow(PdfPTable table, String label, String value, boolean isTotal) {
        Font labelF = isTotal ? TOTAL_FONT : LABEL_FONT;
        Font valueF = isTotal ? TOTAL_FONT : AMOUNT_FONT;

        PdfPCell lc = new PdfPCell(new Phrase(label, labelF));
        lc.setBorder(Rectangle.NO_BORDER);
        lc.setPadding(4);
        lc.setHorizontalAlignment(Element.ALIGN_LEFT);
        if (isTotal) {
            lc.setBackgroundColor(new BaseColor(0xe8, 0xea, 0xf0));
        }
        table.addCell(lc);

        PdfPCell vc = new PdfPCell(new Phrase("\u20B9 " + value, valueF));
        vc.setBorder(Rectangle.NO_BORDER);
        vc.setPadding(4);
        vc.setHorizontalAlignment(Element.ALIGN_RIGHT);
        if (isTotal) {
            vc.setBackgroundColor(new BaseColor(0xe8, 0xea, 0xf0));
        }
        table.addCell(vc);
    }

    private void addFooter(Document doc, Map<String, Object> data) throws DocumentException {
        doc.add(new Paragraph(" "));
        Paragraph line = new Paragraph(new Chunk(new LineSeparator(0.5f, 100, BaseColor.LIGHT_GRAY, Element.ALIGN_CENTER, -2)));
        doc.add(line);
        doc.add(new Paragraph(" "));

        Font footerFont = new Font(Font.FontFamily.HELVETICA, 8, Font.NORMAL, BaseColor.GRAY);

        Paragraph footer1 = new Paragraph(
                "This is a computer-generated statement. No signature is required.",
                footerFont
        );
        footer1.setAlignment(Element.ALIGN_CENTER);
        doc.add(footer1);

        Paragraph footer2 = new Paragraph(
                "For queries, contact customer service: 1800-XXX-XXXX | email: support@bank.com",
                footerFont
        );
        footer2.setAlignment(Element.ALIGN_CENTER);
        doc.add(footer2);

        Paragraph footer3 = new Paragraph(
                "Page 1 of 1",
                footerFont
        );
        footer3.setAlignment(Element.ALIGN_CENTER);
        doc.add(footer3);
    }
}
