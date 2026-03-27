#!/usr/bin/env swift
import Foundation

func readConfig() -> (sessionKey: String, orgId: String)? {
    let configPath = URL(fileURLWithPath: #filePath).deletingLastPathComponent().appendingPathComponent("config.json")
    guard let data = try? Data(contentsOf: configPath),
          let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
          let sk = json["claude_session_key"] as? String, !sk.isEmpty,
          let oid = json["claude_org_id"] as? String, !oid.isEmpty else {
        return nil
    }
    return (sk, oid)
}

func fetch(path: String, sessionKey: String, orgId: String) async throws -> Data {
    guard !orgId.contains(".."), !orgId.contains("/") else {
        throw NSError(domain: "API", code: 5, userInfo: [NSLocalizedDescriptionKey: "Invalid org ID"])
    }
    guard let url = URL(string: "https://claude.ai/api/organizations/\(orgId)/\(path)") else {
        throw NSError(domain: "API", code: 0, userInfo: [NSLocalizedDescriptionKey: "Invalid URL"])
    }
    var req = URLRequest(url: url)
    req.setValue("sessionKey=\(sessionKey)", forHTTPHeaderField: "Cookie")
    req.setValue("application/json", forHTTPHeaderField: "Accept")
    req.httpMethod = "GET"

    let (data, response) = try await URLSession.shared.data(for: req)
    guard let httpResponse = response as? HTTPURLResponse else {
        throw NSError(domain: "API", code: 1, userInfo: [NSLocalizedDescriptionKey: "Not HTTP"])
    }
    guard httpResponse.statusCode == 200 else {
        throw NSError(domain: "API", code: httpResponse.statusCode,
                      userInfo: [NSLocalizedDescriptionKey: "HTTP \(httpResponse.statusCode)"])
    }
    return data
}

Task {
    guard let config = readConfig() else {
        print("{\"error\":\"missing_config\"}")
        exit(1)
    }
    let args = CommandLine.arguments
    let cmd = args.count > 1 ? args[1] : "list"

    do {
        if cmd == "list" {
            let data = try await fetch(path: "chat_conversations", sessionKey: config.sessionKey, orgId: config.orgId)
            if let str = String(data: data, encoding: .utf8) {
                print(str)
            } else {
                print("{\"error\":\"decode_failed\"}")
            }
        } else if cmd == "detail", args.count > 2 {
            let uuid = args[2]
            // Validate UUID format to prevent path traversal
            let uuidRegex = try NSRegularExpression(pattern: "^[0-9a-fA-F-]+$")
            let range = NSRange(uuid.startIndex..<uuid.endIndex, in: uuid)
            guard uuidRegex.firstMatch(in: uuid, range: range) != nil else {
                print("{\"error\":\"invalid_uuid\"}")
                exit(1)
            }
            let data = try await fetch(path: "chat_conversations/\(uuid)", sessionKey: config.sessionKey, orgId: config.orgId)
            if let str = String(data: data, encoding: .utf8) {
                print(str)
            } else {
                print("{\"error\":\"decode_failed\"}")
            }
        } else {
            print("{\"error\":\"unknown_command\"}")
        }
        exit(0)
    } catch {
        print("{\"error\":\"\(error.localizedDescription)\"}")
        exit(1)
    }
}
RunLoop.main.run()
