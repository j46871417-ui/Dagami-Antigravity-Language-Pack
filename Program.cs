using System;
using System.Collections;
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
using System.Web.Script.Serialization;
using System.Windows.Forms;

[assembly: AssemblyTitle("Google Antigravity Localizer")]
[assembly: AssemblyDescription("Google Antigravity Russian Localization Suite")]
[assembly: AssemblyCompany("Open Source Community")]
[assembly: AssemblyProduct("Google Antigravity Localizer")]
[assembly: AssemblyCopyright("Copyright (c) 2026")]
[assembly: AssemblyVersion("0.9.7.0")]
[assembly: AssemblyFileVersion("0.9.7.0")]

namespace AntigravityLocalizer
{
    public static class AppConfig
    {
        public const string Version = "0.9.7";
        public const string TelegramChatUrl = "https://t.me/+8qU7020rMF84OWNi";
    }

    static class Program
    {
        [DllImport("user32.dll")]
        private static extern bool SetForegroundWindow(IntPtr hWnd);

        [DllImport("user32.dll")]
        private static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

        [STAThread]
        static void Main()
        {
            try
            {
                Process current = Process.GetCurrentProcess();
                Process[] existing = Process.GetProcessesByName(current.ProcessName);
                foreach (Process p in existing)
                {
                    if (p.Id != current.Id)
                    {
                        if (p.MainWindowHandle != IntPtr.Zero)
                        {
                            ShowWindow(p.MainWindowHandle, 9); // SW_RESTORE
                            SetForegroundWindow(p.MainWindowHandle);
                            return;
                        }
                        else
                        {
                            try { p.Kill(); } catch { }
                        }
                    }
                }

                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                Application.Run(new MainForm());
            }
            catch (Exception ex)
            {
                MessageBox.Show("Ошибка запуска патчера: " + ex.Message, "Ошибка", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally
            {
                Environment.Exit(0);
            }
        }
    }

    #region Localization Engine

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
                        Log(string.Format("[*] Остановка запущенных процессов {0} ({1} шт.)...", name, procs.Length));
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

        private static void ExtractTranslationPairs(object obj, List<KeyValuePair<string, string>> pairs)
        {
            IDictionary dict = obj as IDictionary;
            if (dict != null)
            {
                if (dict.Contains("en") && dict.Contains("ru"))
                {
                    string en = Convert.ToString(dict["en"]);
                    string ru = Convert.ToString(dict["ru"]);
                    if (!string.IsNullOrEmpty(en) && !string.IsNullOrEmpty(ru))
                    {
                        pairs.Add(new KeyValuePair<string, string>(en, ru));
                    }
                }
                else
                {
                    foreach (DictionaryEntry de in dict)
                    {
                        string sVal = de.Value as string;
                        if (!string.IsNullOrEmpty(sVal))
                        {
                            pairs.Add(new KeyValuePair<string, string>(Convert.ToString(de.Key), sVal));
                        }
                        else
                        {
                            ExtractTranslationPairs(de.Value, pairs);
                        }
                    }
                }
            }
            else
            {
                IEnumerable list = obj as IEnumerable;
                if (list != null && !(obj is string))
                {
                    foreach (object item in list)
                    {
                        ExtractTranslationPairs(item, pairs);
                    }
                }
            }
        }

        public bool Install(bool doDesktop = true, bool doIde = true)
        {
            try
            {
                Log("[*] Начало установки русификатора...");
                KillProcesses();

                Assembly asm = Assembly.GetExecutingAssembly();
                Stream zipStream = asm.GetManifestResourceStream("payload.zip");
                if (zipStream == null)
                {
                    string localZip = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "payload.zip");
                    if (File.Exists(localZip))
                    {
                        zipStream = File.OpenRead(localZip);
                    }
                }

                if (zipStream == null)
                {
                    Log("[-] Ошибка: встроенный архив ресурсов (payload.zip) не найден!");
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
                        int filesExtracted = 0;
                        foreach (ZipArchiveEntry entry in archive.Entries)
                        {
                            string rel = entry.FullName.Replace('\\', '/');

                            if (rel.Equals("resources/app.asar", StringComparison.OrdinalIgnoreCase))
                            {
                                Log("[*] Замена загрузчика Electron (app.asar)...");
                                entry.ExtractToFile(targetAsar, true);
                                Log("[+] app.asar успешно обновлен!");
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
                                    filesExtracted++;
                                }
                            }
                        }
                        Log(string.Format("[+] Скопирован веб-бандл (web_bundle_ru) с 4100+ терминами перевода ({0} файлов)!", filesExtracted));
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

                            ZipArchiveEntry ideTransEntry = archive.GetEntry("translations/ide_strings.json");
                            if (ideTransEntry != null)
                            {
                                using (StreamReader reader = new StreamReader(ideTransEntry.Open(), Encoding.UTF8))
                                {
                                    string transJson = reader.ReadToEnd();
                                    JavaScriptSerializer js = new JavaScriptSerializer();
                                    object root = js.DeserializeObject(transJson);
                                    List<KeyValuePair<string, string>> pairs = new List<KeyValuePair<string, string>>();
                                    ExtractTranslationPairs(root, pairs);

                                    if (pairs.Count > 0)
                                    {
                                        string pkgContent = File.ReadAllText(pkgJsonPath, Encoding.UTF8);
                                        int replaced = 0;
                                        foreach (var kvp in pairs)
                                        {
                                            string search = "\"" + kvp.Key + "\"";
                                            string repl = "\"" + kvp.Value + "\"";
                                            if (pkgContent.Contains(search))
                                            {
                                                pkgContent = pkgContent.Replace(search, repl);
                                                replaced++;
                                            }
                                        }
                                        File.WriteAllText(pkgJsonPath, pkgContent, Encoding.UTF8);
                                        Log(string.Format("[+] Локализовано пунктов в расширении Antigravity IDE: {0}", replaced));
                                    }
                                }
                            }
                            Log("[+] Antigravity IDE успешно русифицирован!");
                        }
                        else
                        {
                            Log("[-] package.json для Antigravity IDE не найден по пути: " + pkgJsonPath);
                        }
                    }
                }

                Log("\n[✓] Установка русификатора завершена успешно!");
                return true;
            }
            catch (Exception ex)
            {
                Log(string.Format("\n[-] Ошибка при установке: {0}", ex.Message));
                return false;
            }
        }

        public bool Restore()
        {
            try
            {
                Log("[*] Восстановление оригинальных файлов...");
                KillProcesses();

                // 1. Desktop
                if (!string.IsNullOrEmpty(DesktopPath) && Directory.Exists(DesktopPath))
                {
                    string resDir = Path.Combine(DesktopPath, "resources");
                    string targetAsar = Path.Combine(resDir, "app.asar");
                    string backupAsar = Path.Combine(resDir, "app.asar.original_backup");

                    if (File.Exists(backupAsar))
                    {
                        File.Copy(backupAsar, targetAsar, true);
                        File.Delete(backupAsar);
                        Log("[+] Оригинальный app.asar успешно восстановлен.");
                    }
                    else
                    {
                        Log("[!] Резервная копия app.asar.original_backup не найдена.");
                    }

                    string webBundleRu = Path.Combine(resDir, "web_bundle_ru");
                    if (Directory.Exists(webBundleRu))
                    {
                        try
                        {
                            Directory.Delete(webBundleRu, true);
                            Log("[+] Каталог web_bundle_ru удален.");
                        }
                        catch { }
                    }
                }

                // 2. IDE
                if (!string.IsNullOrEmpty(IdePath) && Directory.Exists(IdePath))
                {
                    string ideExtDir = Path.Combine(IdePath, @"resources\app\extensions\antigravity");
                    string pkgJsonPath = Path.Combine(ideExtDir, "package.json");
                    string pkgBackup = pkgJsonPath + ".bak.original";

                    if (File.Exists(pkgBackup))
                    {
                        File.Copy(pkgBackup, pkgJsonPath, true);
                        File.Delete(pkgBackup);
                        Log("[+] Оригинальный package.json для Antigravity IDE восстановлен.");
                    }
                }

                Log("\n[✓] Восстановление завершено.");
                return true;
            }
            catch (Exception ex)
            {
                Log(string.Format("\n[-] Ошибка при восстановлении: {0}", ex.Message));
                return false;
            }
        }
    }

    #endregion

    #region Main GUI Form

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
            _engine = new LocalizerEngine(AppendLocalizationLog);
            InitializeComponent();
            RefreshPaths();

            AppendLocalizationLog(string.Format("Google Antigravity Localizer v{0} готов к работе.", AppConfig.Version));
            AppendLocalizationLog("Полная русификация интерфейса, настроек, подсказок и размышлений модели (4100+ терминов).");
            AppendLocalizationLog("Группа сообщества в Telegram: " + AppConfig.TelegramChatUrl + "\n");
        }

        private void InitializeComponent()
        {
            this.Text = string.Format("Google Antigravity Localizer v{0}", AppConfig.Version);
            this.Size = new Size(740, 560);
            this.StartPosition = FormStartPosition.CenterScreen;
            this.FormBorderStyle = FormBorderStyle.FixedSingle;
            this.MaximizeBox = false;
            this.Font = new Font("Segoe UI", 9F, FontStyle.Regular, GraphicsUnit.Point);
            this.BackColor = Color.FromArgb(248, 249, 250);

            // Header Banner
            Panel header = new Panel();
            header.Dock = DockStyle.Top;
            header.Height = 72;
            header.BackColor = Color.FromArgb(24, 43, 73);

            Label title = new Label();
            title.Text = string.Format("Google Antigravity Localizer v{0}", AppConfig.Version);
            title.Font = new Font("Segoe UI", 13F, FontStyle.Bold);
            title.ForeColor = Color.White;
            title.Location = new Point(20, 12);
            title.AutoSize = true;

            Label subtitle = new Label();
            subtitle.Text = "Автономная 100% русификация интерфейса, меню, настроек и размышлений модели";
            subtitle.Font = new Font("Segoe UI", 9F);
            subtitle.ForeColor = Color.FromArgb(180, 205, 235);
            subtitle.Location = new Point(21, 40);
            subtitle.AutoSize = true;

            header.Controls.Add(title);
            header.Controls.Add(subtitle);

            LinkLabel lnkTelegram = new LinkLabel();
            lnkTelegram.Text = "💬 Чат в Telegram";
            lnkTelegram.Font = new Font("Segoe UI", 9.5F, FontStyle.Bold);
            lnkTelegram.LinkColor = Color.FromArgb(100, 181, 246);
            lnkTelegram.ActiveLinkColor = Color.White;
            lnkTelegram.Location = new Point(580, 25);
            lnkTelegram.AutoSize = true;
            lnkTelegram.Cursor = Cursors.Hand;
            lnkTelegram.LinkClicked += (s, e) => {
                try { Process.Start(AppConfig.TelegramChatUrl); } catch { }
            };
            header.Controls.Add(lnkTelegram);
            this.Controls.Add(header);

            // Main Container Panel
            Panel mainPanel = new Panel();
            mainPanel.Location = new Point(15, 82);
            mainPanel.Size = new Size(695, 430);

            // Info Note
            Panel pnlNote = new Panel();
            pnlNote.Location = new Point(0, 0);
            pnlNote.Size = new Size(695, 34);
            pnlNote.BackColor = Color.FromArgb(235, 243, 250);
            Label lblNote = new Label();
            lblNote.Text = "ℹ Переведено более 4100 строк интерфейса, все разделы настроек, подсказки и живой переводчик мыслей.";
            lblNote.Font = new Font("Segoe UI", 8.5F);
            lblNote.ForeColor = Color.FromArgb(30, 70, 120);
            lblNote.Location = new Point(10, 8);
            lblNote.AutoSize = true;
            pnlNote.Controls.Add(lblNote);
            mainPanel.Controls.Add(pnlNote);

            // GroupBox Paths
            GroupBox grpPaths = new GroupBox();
            grpPaths.Text = " Обнаруженные компоненты Antigravity ";
            grpPaths.Location = new Point(0, 42);
            grpPaths.Size = new Size(695, 124);

            // Desktop
            _chkDesktop = new CheckBox();
            _chkDesktop.Text = "Antigravity 2.0 Desktop:";
            _chkDesktop.Location = new Point(15, 24);
            _chkDesktop.Size = new Size(165, 22);
            _chkDesktop.Checked = true;

            _txtDesktopPath = new TextBox();
            _txtDesktopPath.Location = new Point(185, 24);
            _txtDesktopPath.Size = new Size(395, 24);

            _btnBrowseDesktop = new Button();
            _btnBrowseDesktop.Text = "Обзор...";
            _btnBrowseDesktop.Location = new Point(590, 23);
            _btnBrowseDesktop.Size = new Size(90, 26);
            _btnBrowseDesktop.Click += (s, e) => BrowseFolder(true);

            _lblDesktopStatus = new Label();
            _lblDesktopStatus.Location = new Point(185, 50);
            _lblDesktopStatus.Size = new Size(395, 16);
            _lblDesktopStatus.Font = new Font("Segoe UI", 8.25F);

            // IDE
            _chkIde = new CheckBox();
            _chkIde.Text = "Antigravity IDE:";
            _chkIde.Location = new Point(15, 72);
            _chkIde.Size = new Size(165, 22);
            _chkIde.Checked = true;

            _txtIdePath = new TextBox();
            _txtIdePath.Location = new Point(185, 72);
            _txtIdePath.Size = new Size(395, 24);

            _btnBrowseIde = new Button();
            _btnBrowseIde.Text = "Обзор...";
            _btnBrowseIde.Location = new Point(590, 71);
            _btnBrowseIde.Size = new Size(90, 26);
            _btnBrowseIde.Click += (s, e) => BrowseFolder(false);

            _lblIdeStatus = new Label();
            _lblIdeStatus.Location = new Point(185, 98);
            _lblIdeStatus.Size = new Size(395, 16);
            _lblIdeStatus.Font = new Font("Segoe UI", 8.25F);

            grpPaths.Controls.Add(_chkDesktop);
            grpPaths.Controls.Add(_txtDesktopPath);
            grpPaths.Controls.Add(_btnBrowseDesktop);
            grpPaths.Controls.Add(_lblDesktopStatus);

            grpPaths.Controls.Add(_chkIde);
            grpPaths.Controls.Add(_txtIdePath);
            grpPaths.Controls.Add(_btnBrowseIde);
            grpPaths.Controls.Add(_lblIdeStatus);

            mainPanel.Controls.Add(grpPaths);

            // Action Buttons
            _btnInstall = new Button();
            _btnInstall.Text = "✔  Установить русификатор";
            _btnInstall.Location = new Point(0, 174);
            _btnInstall.Size = new Size(390, 42);
            _btnInstall.BackColor = Color.FromArgb(34, 139, 34);
            _btnInstall.ForeColor = Color.White;
            _btnInstall.Font = new Font("Segoe UI", 10F, FontStyle.Bold);
            _btnInstall.FlatStyle = FlatStyle.Flat;
            _btnInstall.FlatAppearance.BorderSize = 0;
            _btnInstall.Cursor = Cursors.Hand;
            _btnInstall.Click += OnInstallClick;

            _btnRestore = new Button();
            _btnRestore.Text = "↺  Откатить к оригиналу";
            _btnRestore.Location = new Point(405, 174);
            _btnRestore.Size = new Size(290, 42);
            _btnRestore.BackColor = Color.FromArgb(220, 224, 230);
            _btnRestore.ForeColor = Color.FromArgb(50, 50, 50);
            _btnRestore.Font = new Font("Segoe UI", 9.5F, FontStyle.Bold);
            _btnRestore.FlatStyle = FlatStyle.Flat;
            _btnRestore.FlatAppearance.BorderSize = 0;
            _btnRestore.Cursor = Cursors.Hand;
            _btnRestore.Click += OnRestoreClick;

            mainPanel.Controls.Add(_btnInstall);
            mainPanel.Controls.Add(_btnRestore);

            // Progress Bar
            _progressBar = new ProgressBar();
            _progressBar.Location = new Point(0, 224);
            _progressBar.Size = new Size(695, 6);
            _progressBar.Style = ProgressBarStyle.Blocks;
            mainPanel.Controls.Add(_progressBar);

            // Log TextBox
            _txtLog = new TextBox();
            _txtLog.Location = new Point(0, 238);
            _txtLog.Size = new Size(695, 190);
            _txtLog.Multiline = true;
            _txtLog.ReadOnly = true;
            _txtLog.ScrollBars = ScrollBars.Vertical;
            _txtLog.BackColor = Color.White;
            _txtLog.Font = new Font("Consolas", 8.5F);
            mainPanel.Controls.Add(_txtLog);

            this.Controls.Add(mainPanel);
        }

        private void RefreshPaths()
        {
            _txtDesktopPath.Text = _engine.DesktopPath ?? "";
            _txtIdePath.Text = _engine.IdePath ?? "";

            if (!string.IsNullOrEmpty(_engine.DesktopPath) && Directory.Exists(_engine.DesktopPath))
            {
                _lblDesktopStatus.Text = "Найдено: " + _engine.DesktopPath;
                _lblDesktopStatus.ForeColor = Color.Green;
                _chkDesktop.Checked = true;
            }
            else
            {
                _lblDesktopStatus.Text = "Не найдено автоматически. Укажите путь вручную.";
                _lblDesktopStatus.ForeColor = Color.Red;
                _chkDesktop.Checked = false;
            }

            if (!string.IsNullOrEmpty(_engine.IdePath) && Directory.Exists(_engine.IdePath))
            {
                _lblIdeStatus.Text = "Найдено: " + _engine.IdePath;
                _lblIdeStatus.ForeColor = Color.Green;
                _chkIde.Checked = true;
            }
            else
            {
                _lblIdeStatus.Text = "Не найдено автоматически. Укажите путь вручную.";
                _lblIdeStatus.ForeColor = Color.FromArgb(180, 100, 0);
                _chkIde.Checked = false;
            }
        }

        private void BrowseFolder(bool isDesktop)
        {
            using (FolderBrowserDialog fbd = new FolderBrowserDialog())
            {
                fbd.Description = isDesktop ? "Выберите каталог с Antigravity.exe" : "Выберите каталог с Antigravity IDE.exe";
                if (fbd.ShowDialog() == DialogResult.OK)
                {
                    if (isDesktop)
                    {
                        _engine.DesktopPath = fbd.SelectedPath;
                    }
                    else
                    {
                        _engine.IdePath = fbd.SelectedPath;
                    }
                    RefreshPaths();
                }
            }
        }

        private void AppendLocalizationLog(string text)
        {
            if (this.InvokeRequired)
            {
                this.Invoke(new Action<string>(AppendLocalizationLog), text);
                return;
            }
            _txtLog.AppendText(text + Environment.NewLine);
        }

        private void OnInstallClick(object sender, EventArgs e)
        {
            if (!_chkDesktop.Checked && !_chkIde.Checked)
            {
                MessageBox.Show("Выберите хотя бы один компонент для установки.", "Внимание", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            _btnInstall.Enabled = false;
            _btnRestore.Enabled = false;
            _progressBar.Style = ProgressBarStyle.Marquee;

            _engine.DesktopPath = _txtDesktopPath.Text.Trim();
            _engine.IdePath = _txtIdePath.Text.Trim();

            bool doDesk = _chkDesktop.Checked;
            bool doIde = _chkIde.Checked;

            ThreadPool.QueueUserWorkItem(state =>
            {
                bool ok = _engine.Install(doDesk, doIde);
                this.Invoke(new Action(() =>
                {
                    _progressBar.Style = ProgressBarStyle.Blocks;
                    _progressBar.Value = ok ? 100 : 0;
                    _btnInstall.Enabled = true;
                    _btnRestore.Enabled = true;

                    if (ok)
                    {
                        MessageBox.Show("Русификатор успешно установлен!\nЗапустите Google Antigravity и проверьте интерфейс.", "Успех", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    }
                    else
                    {
                        MessageBox.Show("При установке возникли ошибки. Проверьте лог в нижней части окна.", "Ошибка", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    }
                }));
            });
        }

        private void OnRestoreClick(object sender, EventArgs e)
        {
            if (MessageBox.Show("Вы действительно хотите восстановить исходные файлы Antigravity?", "Подтверждение", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes)
            {
                return;
            }

            _btnInstall.Enabled = false;
            _btnRestore.Enabled = false;
            _progressBar.Style = ProgressBarStyle.Marquee;

            _engine.DesktopPath = _txtDesktopPath.Text.Trim();
            _engine.IdePath = _txtIdePath.Text.Trim();

            ThreadPool.QueueUserWorkItem(state =>
            {
                bool ok = _engine.Restore();
                this.Invoke(new Action(() =>
                {
                    _progressBar.Style = ProgressBarStyle.Blocks;
                    _progressBar.Value = ok ? 100 : 0;
                    _btnInstall.Enabled = true;
                    _btnRestore.Enabled = true;

                    if (ok)
                    {
                        MessageBox.Show("Оригинальные файлы успешно восстановлены.", "Готово", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    }
                }));
            });
        }

        protected override void OnFormClosed(FormClosedEventArgs e)
        {
            base.OnFormClosed(e);
            Environment.Exit(0);
        }
    }

    #endregion
}
