#!/usr/bin/env swift
import Foundation

// Read config — env vars take priority (for multi-account), then config.json
func readConfig() -> (sessionKey: String, orgId: String)? {
    // Check environment variables first (set by server for multi-account)
    let envSK = ProcessInfo.processInfo.environment["CLAUDE_SESSION_KEY"] ?? ""
    let envOID = ProcessInfo.processInfo.environment["CLAUDE_ORG_ID"] ?? ""
    if !envSK.isEmpty && !envOID.isEmpty {
        return (envSK, envOID)
    }
    // Fall back to config.json
    let configPath = URL(fileURLWithPath: #filePath).deletingLastPathComponent().appendingPathComponent("config.json")
    guard let data = try? Data(contentsOf: configPath),
          let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
          let sk = json["claude_session_key"] as? String, !sk.isEmpty,
          let oid = json["claude_org_id"] as? String, !oid.isEmpty else {
        return nil
    }
    return (sk, oid)
}

func fetchUsage(sessionKey: String, orgId: String) async throws -> Data {
    guard !orgId.contains(".."), !orgId.contains("/") else {
        throw NSError(domain: "ClaudeAPI", code: 5, userInfo: [NSLocalizedDescriptionKey: "Invalid org ID"])
    }
    guard let url = URL(string: "https://claude.ai/api/organizations/\(orgId)/usage") else {
        throw NSError(domain: "ClaudeAPI", code: 0, userInfo: [NSLocalizedDescriptionKey: "Invalid URL"])
    }
    var request = URLRequest(url: url)
    request.setValue("sessionKey=\(sessionKey)", forHTTPHeaderField: "Cookie")
    request.setValue("application/json", forHTTPHeaderField: "Accept")
    request.httpMethod = "GET"

    let (data, response) = try await URLSession.shared.data(for: request)
    guard let httpResponse = response as? HTTPURLResponse else {
        throw NSError(domain: "ClaudeAPI", code: 1, userInfo: [NSLocalizedDescriptionKey: "Not HTTP"])
    }
    guard httpResponse.statusCode == 200 else {
        throw NSError(domain: "ClaudeAPI", code: httpResponse.statusCode,
                      userInfo: [NSLocalizedDescriptionKey: "HTTP \(httpResponse.statusCode)"])
    }
    return data
}

Task {
    guard let config = readConfig() else {
        print("{\"error\":\"missing_config\"}")
        exit(1)
    }
    do {
        let data = try await fetchUsage(sessionKey: config.sessionKey, orgId: config.orgId)
        // Output raw JSON
        if let jsonStr = String(data: data, encoding: .utf8) {
            print(jsonStr)
        } else {
            print("{\"error\":\"decode_failed\"}")
        }
        exit(0)
    } catch {
        print("{\"error\":\"\(error.localizedDescription)\"}")
        exit(1)
    }
}
RunLoop.main.run()
