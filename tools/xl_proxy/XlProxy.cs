using System;
using System.IO;
using System.Reflection;
using System.Text;

// Comarch XL API proxy — x86 subprocess, JSON stdin/stdout
// Komendy: login | logout | dodaj_atrybut | zapytanie | blad
// Format: {"cmd":"...","key":"val",...}\n

class XlProxy {
    static object api;
    static Type apiType;
    static string dllDir;

    static void Main(string[] args) {
        dllDir = args.Length > 0 ? args[0] : @"C:\Comarch ERP\Comarch ERP XL 2025.1";
        string dllPath = Path.Combine(dllDir, "cdn_api20251.net.dll");

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
                case "atrybut":  return CmdAtrybut(json);
                case "zapytanie": return CmdZapytanie(json);
                case "blad":     return CmdBlad();
                default:         return Err("UNKNOWN_CMD", cmd);
            }
        } catch (Exception ex) {
            return Err("DISPATCH_ERROR", ex.Message);
        }
    }

    static string CmdLogin(string json) {
        object info = CreateInfo("cdn_api.XLLoginInfo_20251");
        SetField(info, "Wersja", 20251);
        SetField(info, "TrybWsadowy", 1);
        SetField(info, "ProgramID", "MrowiSkoAgent");
        SetField(info, "Baza",     GetStr(json, "baza"));
        SetField(info, "OpeIdent", GetStr(json, "oper"));
        SetField(info, "OpeHaslo", GetStr(json, "haslo"));
        string serwer = GetStr(json, "serwer");
        if (!string.IsNullOrEmpty(serwer)) SetField(info, "Serwer", serwer);

        int sesjaID = 0;
        object[] pars = new object[] { info, sesjaID };
        MethodInfo m = apiType.GetMethod("XLLogin");
        int ret = (int)m.Invoke(api, pars);
        sesjaID = (int)pars[1];

        if (ret != 0) return Err("LOGIN_FAIL", "kod=" + ret);
        return "{\"ok\":true,\"sesja_id\":" + sesjaID + "}";
    }

    static string CmdLogout(string json) {
        int sesjaID = GetInt(json, "sesja_id");
        MethodInfo m = apiType.GetMethod("XLLogout");
        int ret = (int)m.Invoke(api, new object[] { sesjaID });
        if (ret != 0) return Err("LOGOUT_FAIL", "kod=" + ret);
        return "{\"ok\":true}";
    }

    static string CmdAtrybut(string json) {
        int sesjaID = GetInt(json, "sesja_id");
        object info = CreateInfo("cdn_api.XLAtrybutInfo_20251");
        SetField(info, "Wersja",   20251);
        SetField(info, "GIDTyp",   GetInt(json, "gid_typ"));
        SetField(info, "GIDNumer", GetInt(json, "gid_numer"));
        SetField(info, "GIDFirma", GetInt(json, "gid_firma"));
        SetField(info, "GIDLp",    0);
        SetField(info, "GIDSubLp", 0);
        SetField(info, "Klasa",    GetStr(json, "klasa"));
        SetField(info, "Wartosc",  GetStr(json, "wartosc"));

        MethodInfo m = apiType.GetMethod("XLDodajAtrybut");
        int ret = (int)m.Invoke(api, new object[] { sesjaID, info });

        if (ret != 0) {
            string sBlad = (string)GetFieldVal(info, "sBlad");
            return Err("ATRYBUT_FAIL", "kod=" + ret + " " + (sBlad ?? ""));
        }
        return "{\"ok\":true}";
    }

    static string CmdZapytanie(string json) {
        object info = CreateInfo("cdn_api.XLZapytanie_20251");
        SetField(info, "Wersja",    20251);
        SetField(info, "Zapytanie", GetStr(json, "sql"));

        MethodInfo m = apiType.GetMethod("XLWykonajZapytanie");
        int ret = (int)m.Invoke(api, new object[] { info });

        string kolumny  = (string)GetFieldVal(info, "Kolumny")  ?? "";
        string komunikat = (string)GetFieldVal(info, "Komunikat") ?? "";

        if (ret != 0) return Err("ZAPYTANIE_FAIL", "kod=" + ret + " " + komunikat);
        return "{\"ok\":true,\"kolumny\":" + JsonStr(kolumny) + ",\"wynik\":" + JsonStr(komunikat) + "}";
    }

    static string CmdBlad() {
        object info = CreateInfo("cdn_api.XLKomunikatInfo_20251");
        SetField(info, "Wersja", 20251);
        MethodInfo m = apiType.GetMethod("XLOpisBledu");
        m.Invoke(api, new object[] { info });
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

    static string GetStr(string json, string key) {
        string search = "\"" + key + "\"";
        int idx = json.IndexOf(search);
        if (idx < 0) return "";
        idx = json.IndexOf(':', idx) + 1;
        while (idx < json.Length && json[idx] == ' ') idx++;
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

    static string JsonStr(string s) {
        if (s == null) return "null";
        return "\"" + s.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\r", "\\r").Replace("\n", "\\n") + "\"";
    }

    static string Err(string type, string msg) {
        return "{\"ok\":false,\"error\":{\"type\":" + JsonStr(type) + ",\"message\":" + JsonStr(msg) + "}}";
    }
}
