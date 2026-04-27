using System;
using System.IO;
using System.Reflection;
using System.Text;

// Comarch XL API proxy — x86 subprocess, JSON stdin/stdout
// Komendy: login | logout | invoke | blad
// Format: {"cmd":"...","key":"val",...}\n
// invoke: {"cmd":"invoke","method":"XLNowyDokument","sesja_id":1,"params":{"Wersja":20251,...}}

class XlProxy {
    static object api;
    static Type apiType;
    static string dllDir;

    static void Main(string[] args) {
        dllDir = args.Length > 0 ? args[0] : @"C:\Comarch ERP\Comarch ERP XL 2025.1";
        string dllPath = Path.Combine(dllDir, "cdn_api20251.net.dll");

        Console.OutputEncoding = Encoding.UTF8;
        Console.InputEncoding  = Encoding.UTF8;

        try {
            AppDomain.CurrentDomain.AssemblyResolve += (s, e) => {
                string name = new AssemblyName(e.Name).Name + ".dll";
                string path = Path.Combine(dllDir, name);
                return File.Exists(path) ? Assembly.LoadFrom(path) : null;
            };
            Assembly asm = Assembly.LoadFrom(dllPath);
            apiType = asm.GetType("cdn_api.cdn_api");
            api = Activator.CreateInstance(apiType);
        } catch (Exception ex) {
            Console.WriteLine(Err("LOAD_ERROR", ex.Message));
            return;
        }

        Console.WriteLine("{\"ok\":true,\"msg\":\"proxy ready\"}");
        Console.Out.Flush();

        string line;
        while ((line = Console.ReadLine()) != null) {
            line = line.Trim();
            if (line.Length == 0) continue;
            string result = Dispatch(line);
            Console.WriteLine(result);
            Console.Out.Flush();
        }
    }

    static string Dispatch(string json) {
        try {
            string cmd = GetStr(json, "cmd");
            switch (cmd) {
                case "login":    return CmdLogin(json);
                case "logout":   return CmdLogout(json);
                case "invoke":   return CmdInvoke(json);
                case "describe": return CmdDescribe(json);
                case "blad":     return CmdBlad();
                default:         return Err("UNKNOWN_CMD", cmd);
            }
        } catch (Exception ex) {
            return Err("DISPATCH_ERROR", ex.Message);
        }
    }

    // --- generyczny invoke przez Reflection ---

    static string CmdInvoke(string json) {
        string methodName = GetStr(json, "method");
        if (methodName.Length == 0) return Err("MISSING_METHOD", "");

        MethodInfo m = apiType.GetMethod(methodName);
        if (m == null) return Err("METHOD_NOT_FOUND", methodName);

        int sesjaID    = GetInt(json, "sesja_id");
        string paramsJson = GetObject(json, "params");

        ParameterInfo[] pinfos = m.GetParameters();
        object[] pars = new object[pinfos.Length];

        for (int i = 0; i < pinfos.Length; i++) {
            Type pt    = pinfos[i].ParameterType;
            bool byref = pt.IsByRef;
            if (byref) pt = pt.GetElementType();
            string pname = pinfos[i].Name;

            if (pt == typeof(int)) {
                // Comarch nazwy sesji: _SesjaID, _lSesjaID, sesjaID itp.
                string pLower = pname.ToLower();
                bool isSesja  = pLower == "sesjaid" || pLower.EndsWith("sesjaid");
                pars[i] = isSesja ? sesjaID : GetInt(paramsJson, pname);
            } else {
                object info = Activator.CreateInstance(pt);
                FieldInfo fVer = pt.GetField("Wersja");
                if (fVer != null) fVer.SetValue(info, 20251);
                foreach (FieldInfo f in pt.GetFields()) {
                    string val = GetStr(paramsJson, f.Name);
                    if (val.Length == 0) continue;
                    try { f.SetValue(info, Convert.ChangeType(val, f.FieldType)); } catch { }
                }
                pars[i] = info;
            }
        }

        int ret;
        try { ret = (int)m.Invoke(api, pars); }
        catch (Exception ex) { return Err("INVOKE_ERROR", ex.InnerException != null ? ex.InnerException.Message : ex.Message); }

        if (ret != 0) return Err("INVOKE_FAIL", "kod=" + ret + " method=" + methodName);

        // Serializuj wynik: ref int (out params jak _lDokumentID) + pola struct
        var sb = new StringBuilder("{\"ok\":true,\"data\":{");
        bool first = true;
        for (int i = 0; i < pinfos.Length; i++) {
            Type pt    = pinfos[i].ParameterType;
            bool byref = pt.IsByRef;
            if (byref) pt = pt.GetElementType();
            string pname = pinfos[i].Name;
            string pLower = pname.ToLower();
            bool isSesja  = pLower == "sesjaid" || pLower.EndsWith("sesjaid");

            if (pt == typeof(int)) {
                if (!byref || isSesja) continue;  // pomiń input int i sesja
                // ref int = out param (np. _lDokumentID) — zwróć wartość
                if (!first) sb.Append(",");
                sb.Append(JsonStr(pname)); sb.Append(":"); sb.Append((int)pars[i]);
                first = false;
            } else {
                object info = pars[i];
                foreach (FieldInfo f in pt.GetFields()) {
                    if (!first) sb.Append(",");
                    sb.Append(JsonStr(f.Name)); sb.Append(":"); AppendVal(sb, f.GetValue(info));
                    first = false;
                }
            }
        }
        sb.Append("}}");
        return sb.ToString();
    }

    static void AppendVal(StringBuilder sb, object val) {
        if (val == null) { sb.Append("null"); return; }
        if (val is string) { sb.Append(JsonStr((string)val)); return; }
        if (val is bool)   { sb.Append((bool)val ? "true" : "false"); return; }
        if (val is int || val is long || val is short || val is byte ||
            val is uint || val is ulong || val is ushort || val is sbyte) {
            sb.Append(Convert.ToInt64(val)); return;
        }
        if (val is double || val is float || val is decimal) {
            sb.Append(Convert.ToString(val, System.Globalization.CultureInfo.InvariantCulture)); return;
        }
        sb.Append(JsonStr(val.ToString()));
    }

    // --- describe (diagnostyka) ---

    static string CmdDescribe(string json) {
        string methodName = GetStr(json, "method");
        MethodInfo m = methodName.Length > 0 ? apiType.GetMethod(methodName) : null;
        if (m == null) return Err("METHOD_NOT_FOUND", methodName);

        var sb = new StringBuilder("{\"ok\":true,\"method\":" + JsonStr(methodName) + ",\"params\":[");
        ParameterInfo[] pinfos = m.GetParameters();
        for (int i = 0; i < pinfos.Length; i++) {
            if (i > 0) sb.Append(",");
            Type pt = pinfos[i].ParameterType;
            bool byref = pt.IsByRef;
            if (byref) pt = pt.GetElementType();
            sb.Append("{\"name\":" + JsonStr(pinfos[i].Name));
            sb.Append(",\"type\":" + JsonStr(pt.Name));
            sb.Append(",\"byref\":" + (byref ? "true" : "false"));
            if (!pt.IsPrimitive && pt != typeof(string)) {
                sb.Append(",\"fields\":[");
                FieldInfo[] fields = pt.GetFields();
                for (int j = 0; j < fields.Length; j++) {
                    if (j > 0) sb.Append(",");
                    sb.Append("{\"name\":" + JsonStr(fields[j].Name) + ",\"type\":" + JsonStr(fields[j].FieldType.Name) + "}");
                }
                sb.Append("]");
            }
            sb.Append("}");
        }
        sb.Append("]}");
        return sb.ToString();
    }

    // --- login / logout / blad ---

    static string CmdLogin(string json) {
        object info = CreateInfo("cdn_api.XLLoginInfo_20251");
        SetField(info, "Wersja",     20251);
        string trybStr = GetStr(json, "tryb_wsadowy");
        SetField(info, "TrybWsadowy", trybStr == "0" ? 0 : 1);
        SetField(info, "ProgramID",  "MrowiSkoAgent");
        SetField(info, "Baza",       GetStr(json, "baza"));
        SetField(info, "OpeIdent",   GetStr(json, "oper"));
        SetField(info, "OpeHaslo",   GetStr(json, "haslo"));
        string serwer = GetStr(json, "serwer");
        if (serwer.Length > 0) SetField(info, "Serwer", serwer);

        int sesjaID = 0;
        object[] pars = new object[] { info, sesjaID };
        int ret = (int)apiType.GetMethod("XLLogin").Invoke(api, pars);
        sesjaID = (int)pars[1];

        if (ret != 0) return Err("LOGIN_FAIL", "kod=" + ret);
        return "{\"ok\":true,\"sesja_id\":" + sesjaID + "}";
    }

    static string CmdLogout(string json) {
        int sesjaID = GetInt(json, "sesja_id");
        int ret = (int)apiType.GetMethod("XLLogout").Invoke(api, new object[] { sesjaID });
        if (ret != 0) return Err("LOGOUT_FAIL", "kod=" + ret);
        return "{\"ok\":true}";
    }

    static string CmdBlad() {
        object info = CreateInfo("cdn_api.XLKomunikatInfo_20251");
        SetField(info, "Wersja", 20251);
        apiType.GetMethod("XLOpisBledu").Invoke(api, new object[] { info });
        string opis = (string)GetFieldVal(info, "OpisBledu") ?? "";
        int blad    = (int)(GetFieldVal(info, "Blad") ?? 0);
        return "{\"ok\":true,\"blad\":" + blad + ",\"opis\":" + JsonStr(opis) + "}";
    }

    // --- helpers ---

    static object CreateInfo(string typeName) {
        Type t = apiType.Assembly.GetType(typeName);
        return Activator.CreateInstance(t);
    }

    static void SetField(object obj, string name, object val) {
        FieldInfo f = obj.GetType().GetField(name);
        if (f != null) f.SetValue(obj, Convert.ChangeType(val, f.FieldType));
    }

    static object GetFieldVal(object obj, string name) {
        FieldInfo f = obj.GetType().GetField(name);
        return f != null ? f.GetValue(obj) : null;
    }

    // Wyciąga string lub liczbę jako string z JSON
    static string GetStr(string json, string key) {
        string search = "\"" + key + "\"";
        int idx = json.IndexOf(search);
        if (idx < 0) return "";
        idx = json.IndexOf(':', idx) + 1;
        while (idx < json.Length && json[idx] == ' ') idx++;
        if (idx >= json.Length) return "";
        if (json[idx] == '"') {
            idx++;
            var sb = new StringBuilder();
            while (idx < json.Length && json[idx] != '"') {
                if (json[idx] == '\\' && idx + 1 < json.Length) { idx++; sb.Append(json[idx]); }
                else sb.Append(json[idx]);
                idx++;
            }
            return sb.ToString();
        }
        int end = idx;
        while (end < json.Length && json[end] != ',' && json[end] != '}') end++;
        return json.Substring(idx, end - idx).Trim();
    }

    static int GetInt(string json, string key) {
        string v = GetStr(json, key);
        int i; return int.TryParse(v, out i) ? i : 0;
    }

    // Wyciąga zagnieżdżony obiekt JSON jako string {"k":"v",...}
    static string GetObject(string json, string key) {
        string search = "\"" + key + "\"";
        int idx = json.IndexOf(search);
        if (idx < 0) return "{}";
        idx = json.IndexOf(':', idx) + 1;
        while (idx < json.Length && json[idx] == ' ') idx++;
        if (idx >= json.Length || json[idx] != '{') return "{}";
        int depth = 0, start = idx;
        bool inStr = false;
        while (idx < json.Length) {
            char c = json[idx];
            if (inStr) {
                if (c == '\\') idx++;
                else if (c == '"') inStr = false;
            } else {
                if (c == '"') inStr = true;
                else if (c == '{') depth++;
                else if (c == '}') { depth--; if (depth == 0) return json.Substring(start, idx - start + 1); }
            }
            idx++;
        }
        return "{}";
    }

    static string JsonStr(string s) {
        if (s == null) return "null";
        return "\"" + s.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\r", "\\r").Replace("\n", "\\n") + "\"";
    }

    static string Err(string type, string msg) {
        return "{\"ok\":false,\"error\":{\"type\":" + JsonStr(type) + ",\"message\":" + JsonStr(msg) + "}}";
    }
}
