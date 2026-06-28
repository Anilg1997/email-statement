package com.bankeditor.service;

import com.itextpdf.text.pdf.PdfReader;
import com.itextpdf.text.pdf.PdfStamper;
import com.itextpdf.text.pdf.PdfWriter;
import org.springframework.stereotype.Service;
import java.io.ByteArrayOutputStream;

@Service
public class PdfEncryptionService {

    public byte[] encryptPdf(byte[] pdfData, String userPassword) throws Exception {
        PdfReader reader = new PdfReader(pdfData);
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        PdfStamper stamper = new PdfStamper(reader, baos);
        stamper.setEncryption(
                userPassword.getBytes(),
                "bank_owner_key".getBytes(),
                PdfWriter.ALLOW_PRINTING,
                PdfWriter.ENCRYPTION_AES_256
        );
        stamper.close();
        reader.close();
        return baos.toByteArray();
    }
}
