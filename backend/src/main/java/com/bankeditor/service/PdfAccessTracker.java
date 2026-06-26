package com.bankeditor.service;

import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

@Service
public class PdfAccessTracker {

    private final List<AccessLogEntry> accessLogs = Collections.synchronizedList(new ArrayList<>());
    private final Map<String, Integer> accessCountByAccount = new ConcurrentHashMap<>();

    public void logAccess(String accountId, String ipAddress, String userAgent, String source) {
        AccessLogEntry entry = new AccessLogEntry();
        entry.id = UUID.randomUUID().toString().substring(0, 8);
        entry.accountId = accountId;
        entry.ipAddress = ipAddress;
        entry.userAgent = userAgent;
        entry.source = source;
        entry.timestamp = LocalDateTime.now();
        accessLogs.add(entry);
        accessCountByAccount.merge(accountId, 1, Integer::sum);
    }

    public List<Map<String, Object>> getAccessLogs(String accountId) {
        return accessLogs.stream()
            .filter(log -> accountId == null || accountId.isEmpty() || log.accountId.equals(accountId))
            .sorted((a, b) -> b.timestamp.compareTo(a.timestamp))
            .limit(200)
            .map(log -> {
                Map<String, Object> item = new LinkedHashMap<>();
                item.put("id", log.id);
                item.put("accountId", log.accountId);
                item.put("ipAddress", log.ipAddress);
                item.put("source", log.source);
                item.put("timestamp", log.timestamp.format(DateTimeFormatter.ISO_LOCAL_DATE_TIME));
                item.put("userAgent", truncate(log.userAgent, 80));
                return item;
            })
            .collect(Collectors.toList());
    }

    public int getAccessCount(String accountId) {
        return accessCountByAccount.getOrDefault(accountId, 0);
    }

    public Map<String, Object> getStats() {
        Map<String, Object> stats = new LinkedHashMap<>();
        stats.put("totalAccesses", accessLogs.size());
        stats.put("uniqueAccounts", accessCountByAccount.size());
        stats.put("topAccounts", accessCountByAccount.entrySet().stream()
            .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
            .limit(10)
            .map(e -> Map.of("accountId", e.getKey(), "count", e.getValue()))
            .collect(Collectors.toList()));
        return stats;
    }

    private String truncate(String s, int maxLen) {
        if (s == null) return "";
        return s.length() > maxLen ? s.substring(0, maxLen) + "..." : s;
    }

    static class AccessLogEntry {
        String id;
        String accountId;
        String ipAddress;
        String userAgent;
        String source;
        LocalDateTime timestamp;
    }
}
