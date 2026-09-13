using System.Net;
using System.Web.Script.Serialization;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Windows.Forms;

[assembly: AssemblyTitle("Google Antigravity Localizer")]
[assembly: AssemblyDescription("Google Antigravity Russian Localization Suite")]
[assembly: AssemblyCompany("Open Source")]
[assembly: AssemblyProduct("Google Antigravity Localizer")]
[assembly: AssemblyCopyright("Copyright (c) 2026")]
[assembly: AssemblyVersion("0.0.16.0")]
[assembly: AssemblyFileVersion("0.0.16.0")]

namespace AntigravityLocalizer
{
    public static class AppConfig
    {
        public const string Version = "0.0.16";
    }

    static class Program
    {
        [DllImport("kernel32.dll")]
        static extern bool AttachConsole(int dwProcessId);
        private const int ATTACH_PARENT_PROCESS = -1;

        [STAThread]
        static void Main(string[] args)
        {
            bool cliInstall = false;
            bool cliRestore = false;

            foreach (string a in args)
            {
                string lower = a.ToLowerInvariant();
                if (lower == "--install" || lower == "-i" || lower == "/install") cliInstall = true;
                if (lower == "--restore" || lower == "-r" || lower == "/restore") cliRestore = true;
            }

            if (cliInstall || cliRestore)
            {
                AttachConsole(ATTACH_PARENT_PROCESS);
                Console.WriteLine();
                Console.WriteLine("==========================================================");
                Console.WriteLine(string.Format("      Google Antigravity Localizer v{0} (CLI Mode)        ", AppConfig.Version));
                Console.WriteLine("==========================================================");
                LocalizerEngine engine = new LocalizerEngine(msg => Console.WriteLine(msg));
                if (cliInstall)
                {
                    engine.Install();
                }
                else if (cliRestore)
                {
                    engine.Restore();
                }
                return;
            }

            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new MainForm());
        }
    }

    public class LocalizerEngine
    {
        private Action<string> _logger;
        public string DesktopPath { get; set; }
        public string IdePath { get; set; }

        public LocalizerEngine(Action<string> logger)
        {
            _logger = logger ?? (m => { });
            DetectPaths();
        }

        public void DetectPaths()
        {
            string localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string progFiles = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles);

            // Desktop detection
            string[] desktopCandidates = new string[]
            {
                Path.Combine(localAppData, @"Programs\antigravity"),
                Path.Combine(progFiles, "antigravity"),
                Path.Combine(localAppData, @"Programs\Antigravity")
            };

            foreach (string p in desktopCandidates)
            {
                if (File.Exists(Path.Combine(p, "Antigravity.exe")))
                {
                    DesktopPath = p;
                    break;
                }
            }

            // IDE detection
            string[] ideCandidates = new string[]
            {
                Path.Combine(localAppData, @"Programs\Antigravity IDE"),
                Path.Combine(progFiles, "Antigravity IDE"),
                Path.Combine(localAppData, @"Programs\antigravity-ide")
            };

            foreach (string p in ideCandidates)
            {
                if (File.Exists(Path.Combine(p, "Antigravity.exe")) || File.Exists(Path.Combine(p, "Antigravity IDE.exe")))
                {
                    IdePath = p;
                    break;
                }
            }
        }

        private void Log(string msg)
        {
            _logger(msg);
        }

        public void KillProcesses()
        {
            string[] procNames = new string[] { "Antigravity", "Antigravity IDE" };
            foreach (string name in procNames)
            {
                try
                {
                    Process[] procs = Process.GetProcessesByName(name);
                    if (procs != null && procs.Length > 0)
                    {
                        Log(string.Format("[*] Закрытие запущенных процессов {0} ({1} шт.)...", name, procs.Length));
                        foreach (Process p in procs)
                        {
                            try
                            {
                                p.Kill();
                                p.WaitForExit(3000);
                            }
                            catch { }
                        }
                    }
                }
                catch { }
            }
            Thread.Sleep(500);
        }

        public bool Install(bool doDesktop = true, bool doIde = true)
        {
            try
            {
                Log("[*] Начало установки русификации...");
                KillProcesses();

                Assembly asm = Assembly.GetExecutingAssembly();
                Stream zipStream = asm.GetManifestResourceStream("payload.zip");
                if (zipStream == null)
                {
                    // Fallback to local payload.zip if running unbundled
                    string localZip = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "payload.zip");
                    if (File.Exists(localZip))
                    {
                        zipStream = File.OpenRead(localZip);
                    }
                }

                if (zipStream == null)
                {
                    Log("[-] Ошибка: встроенный языковой пакет (payload.zip) не найден!");
                    return false;
                }

                using (ZipArchive archive = new ZipArchive(zipStream, ZipArchiveMode.Read))
                {
                    // 1. Desktop
                    if (doDesktop && !string.IsNullOrEmpty(DesktopPath) && Directory.Exists(DesktopPath))
                    {
                        Log("\n--- Установка русификации Antigravity 2.0 Desktop ---");
                        string resDir = Path.Combine(DesktopPath, "resources");
                        if (!Directory.Exists(resDir)) Directory.CreateDirectory(resDir);

                        string targetAsar = Path.Combine(resDir, "app.asar");
                        string backupAsar = Path.Combine(resDir, "app.asar.original_backup");

                        // Backup
                        if (File.Exists(targetAsar) && !File.Exists(backupAsar))
                        {
                            Log("[*] Создание резервной копии оригинального app.asar...");
                            File.Copy(targetAsar, backupAsar, true);
                            Log("[+] Бэкап сохранён: app.asar.original_backup");
                        }

                        // Extract app.asar and web_bundle_ru
                        foreach (ZipArchiveEntry entry in archive.Entries)
                        {
                            string rel = entry.FullName.Replace('\\', '/');

                            if (rel.Equals("resources/app.asar", StringComparison.OrdinalIgnoreCase))
                            {
                                Log("[*] Запись локализованного ядра Electron (app.asar)...");
                                entry.ExtractToFile(targetAsar, true);
                                Log("[+] app.asar успешно обновлён!");
                            }
                            else if (rel.StartsWith("resources/web_bundle_ru/", StringComparison.OrdinalIgnoreCase))
                            {
                                string subPath = rel.Substring("resources/web_bundle_ru/".Length);
                                if (!string.IsNullOrEmpty(subPath))
                                {
                                    string destFile = Path.Combine(resDir, "web_bundle_ru", subPath.Replace('/', '\\'));
                                    string destDir = Path.GetDirectoryName(destFile);
                                    if (!Directory.Exists(destDir)) Directory.CreateDirectory(destDir);
                                    entry.ExtractToFile(destFile, true);
                                }
                            }
                        }
                        Log("[+] Языковой веб-бандл (web_bundle_ru) с 950+ фразами установлен!");
                        Log("[+] Antigravity 2.0 Desktop успешно русифицирован!");
                    }

                    // 2. IDE
                    if (doIde && !string.IsNullOrEmpty(IdePath) && Directory.Exists(IdePath))
                    {
                        Log("\n--- Установка русификации Antigravity IDE ---");
                        string ideExtDir = Path.Combine(IdePath, @"resources\app\extensions\antigravity");
                        string pkgJsonPath = Path.Combine(ideExtDir, "package.json");
                        string pkgBackup = pkgJsonPath + ".bak.original";

                        if (File.Exists(pkgJsonPath))
                        {
                            if (!File.Exists(pkgBackup))
                            {
                                File.Copy(pkgJsonPath, pkgBackup, true);
                                Log("[+] Бэкап package.json для IDE сохранён.");
                            }

                            // Read translations from zip
                            ZipArchiveEntry ideTransEntry = archive.GetEntry("translations/ide_strings.json");
                            if (ideTransEntry != null)
                            {
                                string jsonStr;
                                using (StreamReader sr = new StreamReader(ideTransEntry.Open(), Encoding.UTF8))
                                {
                                    jsonStr = sr.ReadToEnd();
                                }

                                string pkgContent = File.ReadAllText(pkgJsonPath, Encoding.UTF8);

                                // Match command titles: "title": "..."
                                MatchCollection cmdMatches = Regex.Matches(jsonStr, "\"([^\"]+)\"\\s*:\\s*\\{\\s*\"ru\"\\s*:\\s*\"([^\"]+)\"", RegexOptions.Singleline);
                                int replaced = 0;
                                foreach (Match m in cmdMatches)
                                {
                                    string cmdId = m.Groups[1].Value;
                                    string ruText = m.Groups[2].Value;

                                    string pattern = "(\"command\"\\s*:\\s*\"" + Regex.Escape(cmdId) + "\"[^}]*\"title\"\\s*:\\s*\")([^\"]+)(\")";
                                    if (Regex.IsMatch(pkgContent, pattern))
                                    {
                                        pkgContent = Regex.Replace(pkgContent, pattern, "${1}" + ruText + "${3}");
                                        replaced++;
                                    }
                                }

                                File.WriteAllText(pkgJsonPath, pkgContent, Encoding.UTF8);
                                Log(string.Format("[+] Обновлено {0} команд Antigravity IDE на русский язык!", replaced));
                            }
                        }
                        Log("[+] Antigravity IDE успешно локализован!");
                    }
                }

                Log("\n==========================================================");
                Log("  Русификация Google Antigravity успешно завершена!");
                Log("==========================================================");
                Log("• Переведено более 950 элементов интерфейса, меню, настроек.");
                Log("• Все проекты, чаты, сессии и ключи API сохранены.");
                Log("• Запустите Antigravity и наслаждайтесь русской версией!");
                Log("• Чат и сообщество в Telegram: https://t.me/+8qU7020rMF84OWNi");
                return true;
            }
            catch (Exception ex)
            {
                Log(string.Format("[-] Ошибка при установке: {0}", ex.Message));
                return false;
            }
        }

        public bool Restore()
        {
            try
            {
                Log("[*] Начало восстановления оригинальных файлов Google...");
                KillProcesses();

                // 1. Desktop restore
                if (!string.IsNullOrEmpty(DesktopPath) && Directory.Exists(DesktopPath))
                {
                    string resDir = Path.Combine(DesktopPath, "resources");
                    string targetAsar = Path.Combine(resDir, "app.asar");
                    string backupAsar = Path.Combine(resDir, "app.asar.original_backup");
                    string bundleDir = Path.Combine(resDir, "web_bundle_ru");

                    if (File.Exists(backupAsar))
                    {
                        File.Copy(backupAsar, targetAsar, true);
                        Log("[+] Оригинальный app.asar успешно восстановлен из резервной копии.");
                    }
                    else
                    {
                        Log("[!] Резервная копия app.asar.original_backup не найдена.");
                    }

                    if (Directory.Exists(bundleDir))
                    {
                        Directory.Delete(bundleDir, true);
                        Log("[+] Каталог web_bundle_ru удалён.");
                    }
                }

                // 2. IDE restore
                if (!string.IsNullOrEmpty(IdePath) && Directory.Exists(IdePath))
                {
                    string ideExtDir = Path.Combine(IdePath, @"resources\app\extensions\antigravity");
                    string pkgJsonPath = Path.Combine(ideExtDir, "package.json");
                    string pkgBackup = pkgJsonPath + ".bak.original";

                    if (File.Exists(pkgBackup))
                    {
                        File.Copy(pkgBackup, pkgJsonPath, true);
                        Log("[+] Оригинальный package.json для IDE восстановлен.");
                    }
                }

                Log("\n==========================================================");
                Log("  Оригинальная версия от Google успешно восстановлена!");
                Log("==========================================================");
                return true;
            }
            catch (Exception ex)
            {
                Log(string.Format("[-] Ошибка при восстановлении: {0}", ex.Message));
                return false;
            }
        }
    }

    public class MainForm : Form
    {
        private LocalizerEngine _engine;
        private Label _lblDesktopStatus;
        private TextBox _txtDesktopPath;
        private Button _btnBrowseDesktop;

        private Label _lblIdeStatus;
        private TextBox _txtIdePath;
        private Button _btnBrowseIde;

        private CheckBox _chkDesktop;
        private CheckBox _chkIde;

        private Button _btnInstall;
        private Button _btnRestore;
        private ProgressBar _progressBar;
        private TextBox _txtLog;
        private AIBridgeServer _bridgeServer;
        private Button _btnManageModels;

        public MainForm()
        {
            InitializeComponent();
            _engine = new LocalizerEngine(AppendLog);
            _bridgeServer = new AIBridgeServer(AppendLog);
            if (_bridgeServer.Settings.AutoStart)
            {
                _bridgeServer.Start();
                // Set environment variable for the session so language_server uses it if launched
                Environment.SetEnvironmentVariable("AGY_API_SERVER_URL", string.Format("http://127.0.0.1:{0}", _bridgeServer.Settings.Port));
            }
            RefreshPaths();
            AppendLog(string.Format("Google Antigravity Localizer v{0} готов к работе.", AppConfig.Version));
            AppendLog("Группа сообщества в Telegram: https://t.me/+8qU7020rMF84OWNi\n");
        }

        private void InitializeComponent()
        {
            this.Text = string.Format("Google Antigravity Localizer v{0} (Русификатор)", AppConfig.Version);
            this.Size = new Size(680, 560);
            this.StartPosition = FormStartPosition.CenterScreen;
            this.FormBorderStyle = FormBorderStyle.FixedSingle;
            this.MaximizeBox = false;
            this.Font = new Font("Segoe UI", 9F, FontStyle.Regular, GraphicsUnit.Point);
            this.BackColor = Color.FromArgb(248, 249, 250);

            // Header Banner
            Panel header = new Panel();
            header.Dock = DockStyle.Top;
            header.Height = 70;
            header.BackColor = Color.FromArgb(24, 43, 73);

            Label title = new Label();
            title.Text = string.Format("Google Antigravity — Русификатор v{0}", AppConfig.Version);
            title.Font = new Font("Segoe UI", 13F, FontStyle.Bold);
            title.ForeColor = Color.White;
            title.Location = new Point(20, 12);
            title.AutoSize = true;

            Label subtitle = new Label();
            subtitle.Text = "Русификация интерфейса (2200+ фраз), перевод ответов ИИ и мыслей на лету!";
            subtitle.Font = new Font("Segoe UI", 9F);
            subtitle.ForeColor = Color.FromArgb(180, 205, 235);
            subtitle.Location = new Point(21, 38);
            subtitle.AutoSize = true;

            header.Controls.Add(title);
            header.Controls.Add(subtitle);

            LinkLabel lnkTelegram = new LinkLabel();
            lnkTelegram.Text = "💬 Чат в Telegram";
            lnkTelegram.Font = new Font("Segoe UI", 9.5F, FontStyle.Bold);
            lnkTelegram.LinkColor = Color.FromArgb(100, 181, 246);
            lnkTelegram.ActiveLinkColor = Color.White;
            lnkTelegram.Location = new Point(490, 24);
            lnkTelegram.AutoSize = true;
            lnkTelegram.Cursor = Cursors.Hand;
            lnkTelegram.LinkClicked += (s, e) => {
                try { Process.Start("https://t.me/+8qU7020rMF84OWNi"); } catch { }
            };
            header.Controls.Add(lnkTelegram);
            this.Controls.Add(header);

            // Main Container
            Panel body = new Panel();
            body.Location = new Point(20, 80);
            body.Size = new Size(625, 430);

            // GroupBox Paths
            GroupBox grpPaths = new GroupBox();
            grpPaths.Text = " Обнаруженные компоненты ";
            grpPaths.Location = new Point(0, 0);
            grpPaths.Size = new Size(625, 125);

            // Desktop
            _chkDesktop = new CheckBox();
            _chkDesktop.Text = "Antigravity 2.0 Desktop:";
            _chkDesktop.Location = new Point(15, 25);
            _chkDesktop.Size = new Size(165, 22);
            _chkDesktop.Checked = true;

            _txtDesktopPath = new TextBox();
            _txtDesktopPath.Location = new Point(185, 25);
            _txtDesktopPath.Size = new Size(330, 23);

            _btnBrowseDesktop = new Button();
            _btnBrowseDesktop.Text = "Обзор...";
            _btnBrowseDesktop.Location = new Point(522, 24);
            _btnBrowseDesktop.Size = new Size(90, 25);
            _btnBrowseDesktop.Click += (s, e) => BrowseFolder(true);

            _lblDesktopStatus = new Label();
            _lblDesktopStatus.Location = new Point(185, 50);
            _lblDesktopStatus.Size = new Size(330, 16);
            _lblDesktopStatus.Font = new Font("Segoe UI", 8.25F);

            // IDE
            _chkIde = new CheckBox();
            _chkIde.Text = "Antigravity IDE:";
            _chkIde.Location = new Point(15, 72);
            _chkIde.Size = new Size(165, 22);
            _chkIde.Checked = true;

            _txtIdePath = new TextBox();
            _txtIdePath.Location = new Point(185, 72);
            _txtIdePath.Size = new Size(330, 23);

            _btnBrowseIde = new Button();
            _btnBrowseIde.Text = "Обзор...";
            _btnBrowseIde.Location = new Point(522, 71);
            _btnBrowseIde.Size = new Size(90, 25);
            _btnBrowseIde.Click += (s, e) => BrowseFolder(false);

            _lblIdeStatus = new Label();
            _lblIdeStatus.Location = new Point(185, 97);
            _lblIdeStatus.Size = new Size(330, 16);
            _lblIdeStatus.Font = new Font("Segoe UI", 8.25F);

            grpPaths.Controls.Add(_chkDesktop);
            grpPaths.Controls.Add(_txtDesktopPath);
            grpPaths.Controls.Add(_btnBrowseDesktop);
            grpPaths.Controls.Add(_lblDesktopStatus);

            grpPaths.Controls.Add(_chkIde);
            grpPaths.Controls.Add(_txtIdePath);
            grpPaths.Controls.Add(_btnBrowseIde);
            grpPaths.Controls.Add(_lblIdeStatus);

            body.Controls.Add(grpPaths);

            // Action Buttons
            _btnInstall = new Button();
            _btnInstall.Text = "✔  Установить русификатор";
            _btnInstall.Location = new Point(0, 135);
            _btnInstall.Size = new Size(340, 42);
            _btnInstall.BackColor = Color.FromArgb(34, 139, 34);
            _btnInstall.ForeColor = Color.White;
            _btnInstall.Font = new Font("Segoe UI", 10.5F, FontStyle.Bold);
            _btnInstall.FlatStyle = FlatStyle.Flat;
            _btnInstall.FlatAppearance.BorderSize = 0;
            _btnInstall.Cursor = Cursors.Hand;
            _btnInstall.Click += OnInstallClick;

            _btnRestore = new Button();
            _btnRestore.Text = "↺  Откатить к оригиналу";
            _btnRestore.Location = new Point(355, 135);
            _btnRestore.Size = new Size(270, 42);
            _btnRestore.BackColor = Color.FromArgb(220, 224, 230);
            _btnRestore.ForeColor = Color.FromArgb(50, 50, 50);
            _btnRestore.Font = new Font("Segoe UI", 9.5F, FontStyle.Bold);
            _btnRestore.FlatStyle = FlatStyle.Flat;
            _btnRestore.FlatAppearance.BorderSize = 0;
            _btnRestore.Cursor = Cursors.Hand;
            _btnRestore.Click += OnRestoreClick;

            _btnManageModels = new Button();
            _btnManageModels.Text = "🤖  Сторонние ИИ-модели (AI Bridge)";
            _btnManageModels.Location = new Point(0, 182);
            _btnManageModels.Size = new Size(625, 34);
            _btnManageModels.BackColor = Color.FromArgb(41, 128, 185);
            _btnManageModels.ForeColor = Color.White;
            _btnManageModels.Font = new Font("Segoe UI", 9.5F, FontStyle.Bold);
            _btnManageModels.FlatStyle = FlatStyle.Flat;
            _btnManageModels.FlatAppearance.BorderSize = 0;
            _btnManageModels.Cursor = Cursors.Hand;
            _btnManageModels.Click += (s, e) => {
                using (ModelsForm mf = new ModelsForm(_bridgeServer)) {
                    mf.ShowDialog(this);
                }
            };

            body.Controls.Add(_btnInstall);
            body.Controls.Add(_btnRestore);
            body.Controls.Add(_btnManageModels);

            // Progress Bar
            _progressBar = new ProgressBar();
            _progressBar.Location = new Point(0, 222);
            _progressBar.Size = new Size(625, 8);
            _progressBar.Style = ProgressBarStyle.Blocks;
            body.Controls.Add(_progressBar);

            // Log TextBox
            _txtLog = new TextBox();
            _txtLog.Location = new Point(0, 235);
            _txtLog.Size = new Size(625, 185);
            _txtLog.Multiline = true;
            _txtLog.ReadOnly = true;
            _txtLog.ScrollBars = ScrollBars.Vertical;
            _txtLog.BackColor = Color.White;
            _txtLog.Font = new Font("Consolas", 8.5F);
            body.Controls.Add(_txtLog);

            this.Controls.Add(body);
        }

        private void RefreshPaths()
        {
            if (!string.IsNullOrEmpty(_engine.DesktopPath))
            {
                _txtDesktopPath.Text = _engine.DesktopPath;
                _lblDesktopStatus.Text = "✓ Обнаружен Antigravity 2.0 Desktop";
                _lblDesktopStatus.ForeColor = Color.FromArgb(34, 139, 34);
                _chkDesktop.Checked = true;
            }
            else
            {
                _txtDesktopPath.Text = "";
                _lblDesktopStatus.Text = "✗ Не найден в стандартном каталоге";
                _lblDesktopStatus.ForeColor = Color.FromArgb(180, 50, 50);
                _chkDesktop.Checked = false;
            }

            if (!string.IsNullOrEmpty(_engine.IdePath))
            {
                _txtIdePath.Text = _engine.IdePath;
                _lblIdeStatus.Text = "✓ Обнаружен Antigravity IDE (VS Code Edition)";
                _lblIdeStatus.ForeColor = Color.FromArgb(34, 139, 34);
                _chkIde.Checked = true;
            }
            else
            {
                _txtIdePath.Text = "";
                _lblIdeStatus.Text = "✗ Не найден в стандартном каталоге";
                _lblIdeStatus.ForeColor = Color.FromArgb(120, 120, 120);
                _chkIde.Checked = false;
            }
        }

        private void BrowseFolder(bool isDesktop)
        {
            using (FolderBrowserDialog fbd = new FolderBrowserDialog())
            {
                fbd.Description = isDesktop ? "Выберите каталог с Antigravity.exe" : "Выберите каталог с Antigravity IDE";
                if (fbd.ShowDialog() == DialogResult.OK)
                {
                    if (isDesktop)
                    {
                        _engine.DesktopPath = fbd.SelectedPath;
                        _txtDesktopPath.Text = fbd.SelectedPath;
                        _lblDesktopStatus.Text = "Выбран пользовательский путь";
                        _lblDesktopStatus.ForeColor = Color.Black;
                        _chkDesktop.Checked = true;
                    }
                    else
                    {
                        _engine.IdePath = fbd.SelectedPath;
                        _txtIdePath.Text = fbd.SelectedPath;
                        _lblIdeStatus.Text = "Выбран пользовательский путь";
                        _lblIdeStatus.ForeColor = Color.Black;
                        _chkIde.Checked = true;
                    }
                }
            }
        }

        public void AppendLog(string text)
        {
            if (this.InvokeRequired)
            {
                this.Invoke(new Action<string>(AppendLog), text);
                return;
            }
            _txtLog.AppendText(text + Environment.NewLine);
        }

        private void SetWorking(bool working)
        {
            _btnInstall.Enabled = !working;
            _btnRestore.Enabled = !working;
            _btnBrowseDesktop.Enabled = !working;
            _btnBrowseIde.Enabled = !working;
            _progressBar.Style = working ? ProgressBarStyle.Marquee : ProgressBarStyle.Blocks;
        }

        private void OnInstallClick(object sender, EventArgs e)
        {
            _engine.DesktopPath = _txtDesktopPath.Text.Trim();
            _engine.IdePath = _txtIdePath.Text.Trim();
            bool doDesktop = _chkDesktop.Checked;
            bool doIde = _chkIde.Checked;

            if (!doDesktop && !doIde)
            {
                MessageBox.Show("Выберите хотя бы один компонент для установки.", "Внимание", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            SetWorking(true);
            _txtLog.Clear();

            ThreadPool.QueueUserWorkItem(_ =>
            {
                bool ok = _engine.Install(doDesktop, doIde);
                this.Invoke(new Action(() =>
                {
                    SetWorking(false);
                    if (ok)
                    {
                        MessageBox.Show("Русификация успешно установлена!\nТеперь можно запускать Google Antigravity.", "Успех", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    }
                    else
                    {
                        MessageBox.Show("При установке возникли ошибки. Проверьте лог.", "Ошибка", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    }
                }));
            });
        }

        private void OnRestoreClick(object sender, EventArgs e)
        {
            DialogResult res = MessageBox.Show(
                "Вы действительно хотите восстановить оригинальную английскую версию Google Antigravity?",
                "Подтверждение",
                MessageBoxButtons.YesNo,
                MessageBoxIcon.Question
            );
            if (res != DialogResult.Yes) return;

            _engine.DesktopPath = _txtDesktopPath.Text.Trim();
            _engine.IdePath = _txtIdePath.Text.Trim();

            SetWorking(true);
            _txtLog.Clear();

            ThreadPool.QueueUserWorkItem(_ =>
            {
                bool ok = _engine.Restore();
                this.Invoke(new Action(() =>
                {
                    SetWorking(false);
                    if (ok)
                    {
                        MessageBox.Show("Оригинальная версия Antigravity успешно восстановлена!", "Восстановление", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    }
                    else
                    {
                        MessageBox.Show("При восстановлении возникли ошибки. Проверьте лог.", "Ошибка", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    }
                }));
            });
        }

        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            if (_bridgeServer != null)
            {
                _bridgeServer.Stop();
            }
            base.OnFormClosing(e);
        }

    

    public class ModelConfig
    {
        public string ModelName { get; set; }        // e.g. "deepseek-chat"
        public string Provider { get; set; }         // "OpenAI", "DeepSeek", "Ollama", "OpenRouter", "Custom"
        public string TargetModel { get; set; }      // e.g. "deepseek-chat" or "llama3:latest"
        public string ApiBase { get; set; }          // e.g. "https://api.deepseek.com/v1" or "http://127.0.0.1:11434/v1"
        public string ApiKey { get; set; }           // encrypted or raw API key
        public bool IsEnabled { get; set; }

        public ModelConfig()
        {
            IsEnabled = true;
        }
    }

    public class BridgeSettings
    {
        public int Port { get; set; }
        public bool AutoStart { get; set; }
        public List<ModelConfig> Models { get; set; }

        public BridgeSettings()
        {
            Port = 51122;
            AutoStart = true;
            Models = new List<ModelConfig>();
        }
    }

    public static class BridgeConfigManager
    {
        private static string ConfigPath
        {
            get
            {
                string dir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "AntigravityLocalizer");
                if (!Directory.Exists(dir)) Directory.CreateDirectory(dir);
                return Path.Combine(dir, "ai_bridge_models.json");
            }
        }

        public static BridgeSettings LoadSettings()
        {
            try
            {
                if (File.Exists(ConfigPath))
                {
                    string json = File.ReadAllText(ConfigPath, Encoding.UTF8);
                    JavaScriptSerializer serializer = new JavaScriptSerializer();
                    BridgeSettings s = serializer.Deserialize<BridgeSettings>(json);
                    if (s != null && s.Models != null) return s;
                }
            }
            catch { }

            BridgeSettings def = new BridgeSettings();
            def.Models.Add(new ModelConfig
            {
                ModelName = "ollama-local",
                Provider = "Ollama",
                TargetModel = "llama3:latest",
                ApiBase = "http://127.0.0.1:11434/v1",
                ApiKey = "ollama",
                IsEnabled = true
            });
            def.Models.Add(new ModelConfig
            {
                ModelName = "deepseek-chat",
                Provider = "DeepSeek",
                TargetModel = "deepseek-chat",
                ApiBase = "https://api.deepseek.com/v1",
                ApiKey = "",
                IsEnabled = true
            });
            SaveSettings(def);
            return def;
        }

        public static void SaveSettings(BridgeSettings settings)
        {
            try
            {
                JavaScriptSerializer serializer = new JavaScriptSerializer();
                string json = serializer.Serialize(settings);
                File.WriteAllText(ConfigPath, json, Encoding.UTF8);
            }
            catch { }
        }
    }

    public class AIBridgeServer
    {
        private HttpListener _listener;
        private Thread _serverThread;
        private bool _isRunning;
        private Action<string> _logger;
        public BridgeSettings Settings { get; set; }

        public bool IsRunning { get { return _isRunning; } }

        public AIBridgeServer(Action<string> logger)
        {
            _logger = logger ?? (m => { });
            Settings = BridgeConfigManager.LoadSettings();
        }

        public void Start()
        {
            if (_isRunning) return;
            try
            {
                _listener = new HttpListener();
                _listener.Prefixes.Add(string.Format("http://127.0.0.1:{0}/", Settings.Port));
                _listener.Start();
                _isRunning = true;
                _serverThread = new Thread(ListenLoop);
                _serverThread.IsBackground = true;
                _serverThread.Start();
                _logger(string.Format("[+] AI Bridge запущен на http://127.0.0.1:{0}/", Settings.Port));
            }
            catch (Exception ex)
            {
                _logger(string.Format("[-] Ошибка запуска AI Bridge: {0}", ex.Message));
                _isRunning = false;
            }
        }

        public void Stop()
        {
            if (!_isRunning) return;
            try
            {
                _isRunning = false;
                if (_listener != null)
                {
                    _listener.Stop();
                    _listener.Close();
                }
                _logger("[*] AI Bridge остановлен.");
            }
            catch { }
        }

        private void ListenLoop()
        {
            while (_isRunning && _listener != null && _listener.IsListening)
            {
                try
                {
                    HttpListenerContext ctx = _listener.GetContext();
                    ThreadPool.QueueUserWorkItem(_ => ProcessRequest(ctx));
                }
                catch
                {
                    if (!_isRunning) break;
                }
            }
        }

        private void ProcessRequest(HttpListenerContext ctx)
        {
            try
            {
                string rawUrl = ctx.Request.RawUrl;
                string method = ctx.Request.HttpMethod;

                // Handle CORS preflight
                if (method == "OPTIONS")
                {
                    ctx.Response.AddHeader("Access-Control-Allow-Origin", "*");
                    ctx.Response.AddHeader("Access-Control-Allow-Methods", "POST, GET, OPTIONS");
                    ctx.Response.AddHeader("Access-Control-Allow-Headers", "*");
                    ctx.Response.StatusCode = 200;
                    ctx.Response.Close();
                    return;
                }

                // Path: /v1beta/models/{modelName}:streamGenerateContent or :generateContent
                if (rawUrl.Contains("/v1beta/models/"))
                {
                    HandleGeminiProxy(ctx);
                }
                else
                {
                    byte[] b = Encoding.UTF8.GetBytes("Antigravity AI Bridge Active.");
                    ctx.Response.ContentType = "text/plain";
                    ctx.Response.OutputStream.Write(b, 0, b.Length);
                    ctx.Response.Close();
                }
            }
            catch (Exception ex)
            {
                _logger(string.Format("[!] Ошибка обработки запроса: {0}", ex.Message));
                try { ctx.Response.StatusCode = 500; ctx.Response.Close(); } catch { }
            }
        }

        private void HandleGeminiProxy(HttpListenerContext ctx)
        {
            string rawUrl = ctx.Request.RawUrl;
            bool isStream = rawUrl.Contains("streamGenerateContent");

            // Extract model name from URL
            // e.g. /v1beta/models/deepseek-chat:streamGenerateContent?alt=sse
            int mIdx = rawUrl.IndexOf("/v1beta/models/");
            string sub = rawUrl.Substring(mIdx + 15);
            int colonIdx = sub.IndexOf(':');
            string modelName = colonIdx > 0 ? sub.Substring(0, colonIdx) : sub.Split('?')[0];

            _logger(string.Format("[AI Bridge] Запрос модели: {0} (stream={1})", modelName, isStream));

            // Read request body
            string reqBody = "";
            using (var reader = new StreamReader(ctx.Request.InputStream, ctx.Request.ContentEncoding))
            {
                reqBody = reader.ReadToEnd();
            }

            // Find configured model
            ModelConfig target = null;
            foreach (var m in Settings.Models)
            {
                if (m.IsEnabled && string.Equals(m.ModelName, modelName, StringComparison.OrdinalIgnoreCase))
                {
                    target = m;
                    break;
                }
            }

            if (target == null && Settings.Models.Count > 0)
            {
                target = Settings.Models[0]; // fallback
            }

            if (target == null)
            {
                byte[] err = Encoding.UTF8.GetBytes("{\"error\":\"Model not configured in AI Bridge\"}");
                ctx.Response.StatusCode = 404;
                ctx.Response.ContentType = "application/json";
                ctx.Response.OutputStream.Write(err, 0, err.Length);
                ctx.Response.Close();
                return;
            }

            // Convert Gemini contents -> OpenAI messages
            JavaScriptSerializer js = new JavaScriptSerializer();
            Dictionary<string, object> geminiReq = null;
            try { geminiReq = js.Deserialize<Dictionary<string, object>>(reqBody); } catch { }

            List<Dictionary<string, string>> openAiMessages = new List<Dictionary<string, string>>();
            if (geminiReq != null && geminiReq.ContainsKey("contents"))
            {
                object[] contents = geminiReq["contents"] as object[];
                if (contents != null)
                {
                    foreach (object cObj in contents)
                    {
                        var cDict = cObj as Dictionary<string, object>;
                        if (cDict == null) continue;
                        string role = cDict.ContainsKey("role") ? Convert.ToString(cDict["role"]) : "user";
                        if (role == "model") role = "assistant";

                        StringBuilder textAccum = new StringBuilder();
                        if (cDict.ContainsKey("parts"))
                        {
                            object[] parts = cDict["parts"] as object[];
                            if (parts != null)
                            {
                                foreach (object pObj in parts)
                                {
                                    var pDict = pObj as Dictionary<string, object>;
                                    if (pDict != null && pDict.ContainsKey("text"))
                                    {
                                        textAccum.AppendLine(Convert.ToString(pDict["text"]));
                                    }
                                }
                            }
                        }

                        openAiMessages.Add(new Dictionary<string, string>
                        {
                            { "role", role },
                            { "content", textAccum.ToString().TrimEnd() }
                        });
                    }
                }
            }

            // Construct OpenAI request
            Dictionary<string, object> openAiReq = new Dictionary<string, object>
            {
                { "model", string.IsNullOrEmpty(target.TargetModel) ? modelName : target.TargetModel },
                { "messages", openAiMessages },
                { "stream", isStream }
            };

            string endpoint = target.ApiBase.TrimEnd('/') + "/chat/completions";
            HttpWebRequest clientReq = (HttpWebRequest)WebRequest.Create(endpoint);
            clientReq.Method = "POST";
            clientReq.ContentType = "application/json";
            if (!string.IsNullOrEmpty(target.ApiKey))
            {
                clientReq.Headers["Authorization"] = "Bearer " + target.ApiKey;
            }

            byte[] outData = Encoding.UTF8.GetBytes(js.Serialize(openAiReq));
            clientReq.ContentLength = outData.Length;
            using (Stream reqStream = clientReq.GetRequestStream())
            {
                reqStream.Write(outData, 0, outData.Length);
            }

            // Forward response
            try
            {
                using (HttpWebResponse clientResp = (HttpWebResponse)clientReq.GetResponse())
                {
                    ctx.Response.AddHeader("Access-Control-Allow-Origin", "*");
                    ctx.Response.StatusCode = 200;

                    if (isStream)
                    {
                        ctx.Response.ContentType = "text/event-stream";
                        ctx.Response.SendChunked = true;

                        using (Stream s = clientResp.GetResponseStream())
                        using (StreamReader sr = new StreamReader(s, Encoding.UTF8))
                        using (StreamWriter sw = new StreamWriter(ctx.Response.OutputStream, Encoding.UTF8))
                        {
                            string line;
                            while ((line = sr.ReadLine()) != null)
                            {
                                string trimmed = line.Trim();
                                if (!trimmed.StartsWith("data:")) continue;
                                string payload = trimmed.Substring(5).Trim();
                                if (payload == "[DONE]") break;

                                try
                                {
                                    var chunkDict = js.Deserialize<Dictionary<string, object>>(payload);
                                    if (chunkDict != null && chunkDict.ContainsKey("choices"))
                                    {
                                        object[] choices = chunkDict["choices"] as object[];
                                        if (choices != null && choices.Length > 0)
                                        {
                                            var firstChoice = choices[0] as Dictionary<string, object>;
                                            if (firstChoice != null && firstChoice.ContainsKey("delta"))
                                            {
                                                var delta = firstChoice["delta"] as Dictionary<string, object>;
                                                if (delta != null && delta.ContainsKey("content"))
                                                {
                                                    string cText = Convert.ToString(delta["content"]);
                                                    if (!string.IsNullOrEmpty(cText))
                                                    {
                                                        var gChunk = new Dictionary<string, object>
                                                        {
                                                            {
                                                                "candidates", new object[]
                                                                {
                                                                    new Dictionary<string, object>
                                                                    {
                                                                        { "content", new Dictionary<string, object> { { "parts", new object[] { new Dictionary<string, object> { { "text", cText } } } }, { "role", "model" } } }
                                                                    }
                                                                }
                                                            }
                                                        };
                                                        sw.Write("data: " + js.Serialize(gChunk) + "\n\n");
                                                        sw.Flush();
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                                catch { }
                            }
                        }
                    }
                    else
                    {
                        using (Stream s = clientResp.GetResponseStream())
                        using (StreamReader sr = new StreamReader(s, Encoding.UTF8))
                        {
                            string respText = sr.ReadToEnd();
                            var oResp = js.Deserialize<Dictionary<string, object>>(respText);
                            string finalContent = "";
                            if (oResp != null && oResp.ContainsKey("choices"))
                            {
                                object[] choices = oResp["choices"] as object[];
                                if (choices != null && choices.Length > 0)
                                {
                                    var ch = choices[0] as Dictionary<string, object>;
                                    if (ch != null && ch.ContainsKey("message"))
                                    {
                                        var msg = ch["message"] as Dictionary<string, object>;
                                        if (msg != null && msg.ContainsKey("content"))
                                        {
                                            finalContent = Convert.ToString(msg["content"]);
                                        }
                                    }
                                }
                            }

                            var gResp = new Dictionary<string, object>
                            {
                                {
                                    "candidates", new object[]
                                    {
                                        new Dictionary<string, object>
                                        {
                                            { "content", new Dictionary<string, object> { { "parts", new object[] { new Dictionary<string, object> { { "text", finalContent } } } }, { "role", "model" } } }
                                        }
                                    }
                                }
                            };
                            byte[] gBytes = Encoding.UTF8.GetBytes(js.Serialize(gResp));
                            ctx.Response.ContentType = "application/json";
                            ctx.Response.ContentLength64 = gBytes.Length;
                            ctx.Response.OutputStream.Write(gBytes, 0, gBytes.Length);
                        }
                    }
                }
            }
            catch (WebException wex)
            {
                _logger(string.Format("[AI Bridge Error]: {0}", wex.Message));
                ctx.Response.StatusCode = 502;
                byte[] err = Encoding.UTF8.GetBytes("{\"error\":\"" + wex.Message + "\"}");
                ctx.Response.OutputStream.Write(err, 0, err.Length);
            }
            finally
            {
                try { ctx.Response.Close(); } catch { }
            }
        }
    }


    public class ModelsForm : Form
    {
        private ListView _lvModels;
        private Button _btnAdd;
        private Button _btnEdit;
        private Button _btnDelete;
        private Button _btnTest;
        private Button _btnToggleServer;
        private Label _lblServerStatus;
        private BridgeSettings _settings;
        private AIBridgeServer _server;

        public ModelsForm(AIBridgeServer server)
        {
            _server = server;
            _settings = _server.Settings;
            InitializeComponent();
            LoadModelsToListView();
            UpdateServerStatusUI();
        }

        private void InitializeComponent()
        {
            this.Text = "Управление сторонними ИИ-моделями (AI Bridge)";
            this.Size = new Size(720, 500);
            this.StartPosition = FormStartPosition.CenterParent;
            this.Font = new Font("Segoe UI", 9F);
            this.BackColor = Color.FromArgb(248, 249, 250);

            // Server status bar
            Panel pnlTop = new Panel();
            pnlTop.Dock = DockStyle.Top;
            pnlTop.Height = 55;
            pnlTop.BackColor = Color.FromArgb(240, 243, 246);

            _lblServerStatus = new Label();
            _lblServerStatus.Location = new Point(15, 18);
            _lblServerStatus.AutoSize = true;
            _lblServerStatus.Font = new Font("Segoe UI", 10F, FontStyle.Bold);

            _btnToggleServer = new Button();
            _btnToggleServer.Location = new Point(520, 12);
            _btnToggleServer.Size = new Size(165, 32);
            _btnToggleServer.FlatStyle = FlatStyle.Flat;
            _btnToggleServer.Font = new Font("Segoe UI", 9F, FontStyle.Bold);
            _btnToggleServer.Click += (s, e) =>
            {
                if (_server.IsRunning) _server.Stop();
                else _server.Start();
                UpdateServerStatusUI();
            };

            pnlTop.Controls.Add(_lblServerStatus);
            pnlTop.Controls.Add(_btnToggleServer);
            this.Controls.Add(pnlTop);

            // Models list view
            _lvModels = new ListView();
            _lvModels.Location = new Point(15, 70);
            _lvModels.Size = new Size(540, 370);
            _lvModels.View = View.Details;
            _lvModels.FullRowSelect = true;
            _lvModels.GridLines = true;
            _lvModels.Columns.Add("Имя в Antigravity", 120);
            _lvModels.Columns.Add("URL для Antigravity", 180);
            _lvModels.Columns.Add("Провайдер", 90);
            _lvModels.Columns.Add("Целевая модель", 120);
            _lvModels.Columns.Add("API Base", 130);
            this.Controls.Add(_lvModels);

            // Right side buttons
            int bx = 570, by = 70;
            _btnAdd = new Button();
            _btnAdd.Text = "➕ Добавить...";
            _btnAdd.Location = new Point(bx, by);
            _btnAdd.Size = new Size(125, 32);
            _btnAdd.Click += OnAddModel;
            this.Controls.Add(_btnAdd);

            by += 40;
            _btnEdit = new Button();
            _btnEdit.Text = "✏ Изменить...";
            _btnEdit.Location = new Point(bx, by);
            _btnEdit.Size = new Size(125, 32);
            _btnEdit.Click += OnEditModel;
            this.Controls.Add(_btnEdit);

            by += 40;
            _btnDelete = new Button();
            _btnDelete.Text = "🗑 Удалить";
            _btnDelete.Location = new Point(bx, by);
            _btnDelete.Size = new Size(125, 32);
            _btnDelete.Click += OnDeleteModel;
            this.Controls.Add(_btnDelete);

            by += 40;
            _btnTest = new Button();
            _btnTest.Text = "⚡ Проверить API";
            _btnTest.Location = new Point(bx, by);
            _btnTest.Size = new Size(125, 32);
            _btnTest.Click += OnTestModel;
            this.Controls.Add(_btnTest);

            by += 45;
            Button btnCopyUrl = new Button();
            btnCopyUrl.Text = "📋 Скопировать URL";
            btnCopyUrl.Location = new Point(bx, by);
            btnCopyUrl.Size = new Size(125, 36);
            btnCopyUrl.Click += (s, e) => {
                if (_lvModels.SelectedItems.Count > 0) {
                    ModelConfig m = _lvModels.SelectedItems[0].Tag as ModelConfig;
                    if (m != null) {
                        string u = "gemini-api:/models/" + m.ModelName;
                        Clipboard.SetText(u);
                        MessageBox.Show("URL скопирован в буфер обмена:\n\n" + u + "\n\nВставьте его в Antigravity в поле «URL модели».", "Скопировано", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    }
                } else {
                    MessageBox.Show("Выберите модель из списка, чтобы скопировать её URL для Antigravity.", "Информация", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
            };
            this.Controls.Add(btnCopyUrl);
        }

        private void UpdateServerStatusUI()
        {
            if (_server.IsRunning)
            {
                _lblServerStatus.Text = string.Format("🟢 AI Bridge активен на порту {0}", _server.Settings.Port);
                _lblServerStatus.ForeColor = Color.FromArgb(34, 139, 34);
                _btnToggleServer.Text = "Остановить мост";
                _btnToggleServer.BackColor = Color.FromArgb(230, 100, 100);
                _btnToggleServer.ForeColor = Color.White;
            }
            else
            {
                _lblServerStatus.Text = "🔴 AI Bridge остановлен";
                _lblServerStatus.ForeColor = Color.FromArgb(180, 50, 50);
                _btnToggleServer.Text = "Запустить мост";
                _btnToggleServer.BackColor = Color.FromArgb(34, 139, 34);
                _btnToggleServer.ForeColor = Color.White;
            }
        }

        private void LoadModelsToListView()
        {
            _lvModels.Items.Clear();
            foreach (var m in _settings.Models)
            {
                ListViewItem item = new ListViewItem(m.ModelName);
                item.SubItems.Add("gemini-api:/models/" + m.ModelName);
                item.SubItems.Add(m.Provider);
                item.SubItems.Add(m.TargetModel);
                item.SubItems.Add(m.ApiBase);
                item.Tag = m;
                _lvModels.Items.Add(item);
            }
        }

        private void OnAddModel(object sender, EventArgs e)
        {
            using (EditModelDialog dlg = new EditModelDialog(null))
            {
                if (dlg.ShowDialog(this) == DialogResult.OK)
                {
                    _settings.Models.Add(dlg.Config);
                    BridgeConfigManager.SaveSettings(_settings);
                    LoadModelsToListView();
                }
            }
        }

        private void OnEditModel(object sender, EventArgs e)
        {
            if (_lvModels.SelectedItems.Count == 0) return;
            ModelConfig cur = _lvModels.SelectedItems[0].Tag as ModelConfig;
            if (cur == null) return;

            using (EditModelDialog dlg = new EditModelDialog(cur))
            {
                if (dlg.ShowDialog(this) == DialogResult.OK)
                {
                    BridgeConfigManager.SaveSettings(_settings);
                    LoadModelsToListView();
                }
            }
        }

        private void OnDeleteModel(object sender, EventArgs e)
        {
            if (_lvModels.SelectedItems.Count == 0) return;
            ModelConfig cur = _lvModels.SelectedItems[0].Tag as ModelConfig;
            if (cur == null) return;

            if (MessageBox.Show(string.Format("Удалить модель «{0}»?", cur.ModelName), "Подтверждение", MessageBoxButtons.YesNo, MessageBoxIcon.Question) == DialogResult.Yes)
            {
                _settings.Models.Remove(cur);
                BridgeConfigManager.SaveSettings(_settings);
                LoadModelsToListView();
            }
        }

        private void OnTestModel(object sender, EventArgs e)
        {
            if (_lvModels.SelectedItems.Count == 0)
            {
                MessageBox.Show("Выберите модель из списка для проверки.", "Информация", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }
            ModelConfig cur = _lvModels.SelectedItems[0].Tag as ModelConfig;
            if (cur == null) return;

            if (string.IsNullOrEmpty(cur.ApiKey) && !cur.Provider.StartsWith("Ollama"))
            {
                MessageBox.Show("Для облачной модели «" + cur.ModelName + "» (" + cur.Provider + ") не задан API-ключ!\n\nНажмите кнопку «Изменить...» и вставьте ваш API-ключ (sk-...).", "Отсутствует API-ключ", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            Cursor.Current = Cursors.WaitCursor;
            try
            {
                string endpoint = cur.ApiBase.TrimEnd('/') + "/chat/completions";
                HttpWebRequest req = (HttpWebRequest)WebRequest.Create(endpoint);
                req.Method = "POST";
                req.ContentType = "application/json";
                req.Timeout = 12000;
                if (!string.IsNullOrEmpty(cur.ApiKey))
                {
                    req.Headers["Authorization"] = "Bearer " + cur.ApiKey;
                }

                JavaScriptSerializer js = new JavaScriptSerializer();
                var body = new Dictionary<string, object>
                {
                    { "model", string.IsNullOrEmpty(cur.TargetModel) ? cur.ModelName : cur.TargetModel },
                    { "messages", new object[] { new Dictionary<string, string> { { "role", "user" }, { "content", "ping" } } } },
                    { "max_tokens", 5 }
                };

                byte[] b = Encoding.UTF8.GetBytes(js.Serialize(body));
                req.ContentLength = b.Length;
                using (Stream s = req.GetRequestStream()) s.Write(b, 0, b.Length);

                using (HttpWebResponse resp = (HttpWebResponse)req.GetResponse())
                {
                    Cursor.Current = Cursors.Default;
                    MessageBox.Show(string.Format("✓ Успешное подключение к «{0}»!\nКод ответа: {1}\n\nМодель доступна и отвечает.", cur.ModelName, resp.StatusCode), "Тест API успешен", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
            }
            catch (WebException wex)
            {
                Cursor.Current = Cursors.Default;
                string details = "";
                try
                {
                    if (wex.Response != null)
                    {
                        using (var reader = new StreamReader(wex.Response.GetResponseStream()))
                        {
                            details = reader.ReadToEnd();
                        }
                    }
                }
                catch { }

                string msg = wex.Message;
                if (!string.IsNullOrEmpty(details))
                {
                    msg += "\n\nПодробности от сервера:\n" + details;
                }
                if (wex.Message.Contains("401"))
                {
                    msg += "\n\n(Ошибка 401 означает: неверный или отсутствующий API-ключ. Проверьте ключ в настройках модели).";
                }
                MessageBox.Show("✗ Ошибка подключения к " + cur.ModelName + ":\n\n" + msg, "Ошибка теста API", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            catch (Exception ex)
            {
                Cursor.Current = Cursors.Default;
                MessageBox.Show(string.Format("✗ Ошибка подключения:\n{0}", ex.Message), "Ошибка теста API", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }
    }

    public class EditModelDialog : Form
    {
        public ModelConfig Config { get; private set; }

        private TextBox _txtModelName;
        private ComboBox _cmbProvider;
        private TextBox _txtTargetModel;
        private TextBox _txtApiBase;
        private TextBox _txtApiKey;

        public EditModelDialog(ModelConfig existing)
        {
            Config = existing ?? new ModelConfig();
            InitializeComponent();
            if (existing != null)
            {
                _txtModelName.Text = existing.ModelName;
                _cmbProvider.SelectedItem = existing.Provider;
                _txtTargetModel.Text = existing.TargetModel;
                _txtApiBase.Text = existing.ApiBase;
                _txtApiKey.Text = existing.ApiKey;
            }
            else
            {
                _cmbProvider.SelectedIndex = 0;
            }
        }

        private void InitializeComponent()
        {
            this.Text = "Настройка ИИ-модели";
            this.Size = new Size(480, 340);
            this.StartPosition = FormStartPosition.CenterParent;
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.Font = new Font("Segoe UI", 9F);

            int lx = 20, tx = 160, y = 20;

            // Model name in Antigravity
            Label l1 = new Label { Text = "Имя в Antigravity:", Location = new Point(lx, y), AutoSize = true };
            _txtModelName = new TextBox { Location = new Point(tx, y), Size = new Size(280, 23) };
            this.Controls.Add(l1); this.Controls.Add(_txtModelName);

            Label lblUrlHint = new Label { Location = new Point(tx, y + 24), Size = new Size(280, 16), ForeColor = Color.FromArgb(100, 100, 100), Font = new Font("Segoe UI", 7.8F) };
            _txtModelName.TextChanged += (s, e) => {
                string nm = _txtModelName.Text.Trim();
                lblUrlHint.Text = "URL для Antigravity: gemini-api:/models/" + (string.IsNullOrEmpty(nm) ? "..." : nm);
            };
            string curNm = _txtModelName.Text.Trim();
            lblUrlHint.Text = "URL для Antigravity: gemini-api:/models/" + (string.IsNullOrEmpty(curNm) ? "..." : curNm);
            this.Controls.Add(lblUrlHint);
            y += 18;

            // Provider
            y += 38;
            Label l2 = new Label { Text = "Провайдер:", Location = new Point(lx, y), AutoSize = true };
            _cmbProvider = new ComboBox { Location = new Point(tx, y), Size = new Size(280, 23), DropDownStyle = ComboBoxStyle.DropDownList };
            _cmbProvider.Items.AddRange(new object[] { "Ollama (Локальный)", "DeepSeek", "OpenAI", "OpenRouter", "Custom" });
            _cmbProvider.SelectedIndexChanged += OnProviderChanged;
            this.Controls.Add(l2); this.Controls.Add(_cmbProvider);

            // Target Model
            y += 38;
            Label l3 = new Label { Text = "ID модели (API):", Location = new Point(lx, y), AutoSize = true };
            _txtTargetModel = new TextBox { Location = new Point(tx, y), Size = new Size(280, 23) };
            this.Controls.Add(l3); this.Controls.Add(_txtTargetModel);

            // API Base
            y += 38;
            Label l4 = new Label { Text = "Базовый URL:", Location = new Point(lx, y), AutoSize = true };
            _txtApiBase = new TextBox { Location = new Point(tx, y), Size = new Size(280, 23) };
            this.Controls.Add(l4); this.Controls.Add(_txtApiBase);

            // API Key
            y += 38;
            Label l5 = new Label { Text = "API Ключ:", Location = new Point(lx, y), AutoSize = true };
            _txtApiKey = new TextBox { Location = new Point(tx, y), Size = new Size(280, 23), UseSystemPasswordChar = true };
            this.Controls.Add(l5); this.Controls.Add(_txtApiKey);

            // Buttons
            y += 45;
            Button btnOk = new Button { Text = "Сохранить", Location = new Point(230, y), Size = new Size(100, 30), DialogResult = DialogResult.OK };
            btnOk.Click += (s, e) =>
            {
                Config.ModelName = _txtModelName.Text.Trim();
                Config.Provider = _cmbProvider.SelectedItem.ToString();
                Config.TargetModel = _txtTargetModel.Text.Trim();
                Config.ApiBase = _txtApiBase.Text.Trim();
                Config.ApiKey = _txtApiKey.Text.Trim();
            };

            Button btnCancel = new Button { Text = "Отмена", Location = new Point(340, y), Size = new Size(100, 30), DialogResult = DialogResult.Cancel };

            this.Controls.Add(btnOk);
            this.Controls.Add(btnCancel);
            this.AcceptButton = btnOk;
            this.CancelButton = btnCancel;
        }

        private void OnProviderChanged(object sender, EventArgs e)
        {
            string p = _cmbProvider.SelectedItem.ToString();
            if (p.StartsWith("Ollama"))
            {
                if (string.IsNullOrEmpty(_txtApiBase.Text)) _txtApiBase.Text = "http://127.0.0.1:11434/v1";
                if (string.IsNullOrEmpty(_txtTargetModel.Text)) _txtTargetModel.Text = "llama3:latest";
                _txtApiKey.Text = "ollama";
            }
            else if (p == "DeepSeek")
            {
                if (string.IsNullOrEmpty(_txtApiBase.Text) || _txtApiBase.Text.Contains("11434")) _txtApiBase.Text = "https://api.deepseek.com/v1";
                if (string.IsNullOrEmpty(_txtTargetModel.Text) || _txtTargetModel.Text.Contains("llama")) _txtTargetModel.Text = "deepseek-chat";
            }
            else if (p == "OpenAI")
            {
                if (string.IsNullOrEmpty(_txtApiBase.Text) || _txtApiBase.Text.Contains("deepseek") || _txtApiBase.Text.Contains("11434")) _txtApiBase.Text = "https://api.openai.com/v1";
                if (string.IsNullOrEmpty(_txtTargetModel.Text) || _txtTargetModel.Text.Contains("llama") || _txtTargetModel.Text.Contains("deepseek")) _txtTargetModel.Text = "gpt-4o";
            }
            else if (p == "OpenRouter")
            {
                if (string.IsNullOrEmpty(_txtApiBase.Text)) _txtApiBase.Text = "https://openrouter.ai/api/v1";
            }
        }
    }


}
}
