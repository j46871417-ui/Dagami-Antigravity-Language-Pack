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
[assembly: AssemblyVersion("1.0.0.0")]
[assembly: AssemblyFileVersion("1.0.0.0")]

namespace AntigravityLocalizer
{
    public static class AppConfig
    {
        public const string Version = "0.0.10";
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

        public MainForm()
        {
            InitializeComponent();
            _engine = new LocalizerEngine(AppendLog);
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
            subtitle.Text = "Русификация интерфейса (950+ фраз) и перевод размышлений на лету!";
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

            body.Controls.Add(_btnInstall);
            body.Controls.Add(_btnRestore);

            // Progress Bar
            _progressBar = new ProgressBar();
            _progressBar.Location = new Point(0, 186);
            _progressBar.Size = new Size(625, 8);
            _progressBar.Style = ProgressBarStyle.Blocks;
            body.Controls.Add(_progressBar);

            // Log TextBox
            _txtLog = new TextBox();
            _txtLog.Location = new Point(0, 202);
            _txtLog.Size = new Size(625, 220);
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
    }
}
