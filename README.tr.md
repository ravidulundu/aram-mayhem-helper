# ARAM Mayhem Helper — Türkçe

[Ana sayfa](README.md) · **Türkçe** · [English](README.en.md)

League of Legends **ARAM Mayhem** için yerel Windows yardımcı uygulaması. Python motoru maç durumunu ve eklenti tekliflerini okur; Electron arayüzü önerileri oyun üzerinde gösterir. Overwolf veya ayrı bir yardımcı hizmet hesabı gerektirmez. Arayüz, eşya ve eklenti adları İngilizcedir; mevcut OCR akışı için oyunu İngilizce kullanın.

## Projenin kökeni ve yerel katkılar

Orijinal proje **Joltarise / CyberKird** tarafından geliştirildi: [orijinal depo](https://github.com/CyberKird/aram-mayhem-helper). Bu çalışma kopyası [ravidulundu fork'una](https://github.com/ravidulundu/aram-mayhem-helper) aittir. Özgün mimari ve özelliklerin sahipliği geliştiricisinde kalır; yerel katkılar ayrıca belgelenir ve resmî bir orijinal proje sürümü değildir. Ana README, özgün belgenin dili olan Romence kalır.

Yerel katkılar; İngilizce arayüzü, görev çubuğu erişimini, altı eşya planını ve uyumluluk korumalarını, duruma göre karşı eşya adaylarını, daha açık eklenti istatistiği açıklamalarını, atomik veri güncellemelerini, ETag önbelleği ve oyuncu/takım fallback düzeltmelerini ve yerel kalite kontrollerini kapsar. Romence ana README'ye İngilizce ve Türkçe belgeler eşlik eder.

Bu değişiklikler fork sürümü olarak yayımlanmadı. Başlıkta hâlâ `2.0.7` görünebilir; bu numara tek başına yerel değişiklikleri tanımlamaz. Geliştirme bilgisayarındaki masaüstü kısayolu artık doğrulanmış yerel motoru `--no-update` ile kullanır; önceki motor ve kısayol yedeklendi. Bu bilgisayara özel kurulum, orijinal yükleyicileri değiştirmez ve başka bir bilgisayara bu değişiklikleri kurmaz.

Fork'a özel sorunları ravidulundu fork'unda takip et. Mevcut bildirim formu hâlâ orijinal geliştiricinin adresini kullanır; bu fork onun desteği veya onayı anlamına gelmez.

## Özellikler

- Sana atanan şampiyon, OCR ile algılanan kişisel kartlar ve ortak bench için şampiyon seçimi sıralaması; en iyi adayın vurgulanması.
- Veri bulunduğunda şampiyon kazanma/seçilme oranları, yama karşılaştırmaları ve denge değişiklikleri.
- Çizmeler dahil en fazla altı hedef eşyalık plan; sahip olunan eşyalar ve eklentinin gerektirdiği alışverişler hesaba katılır.
- Rakiplerin aldığı eşyalara ve kompozisyona dayanan karşı eşya kuralları. MR satın alımına karşı yüzde büyü nüfuzu adayları kullanılır.
- Planlanan eşyalar arasında uyumluluk kontrolü; desteklenen eklenti görevleri ve tekrar alınabilen eşyalar için istisnalar.
- İyileştirmeye karşı bütün ilgili kurallarda takımın anti-heal eşyalarını kontrol etme; dönüşen eşyaları takip etme.
- Şampiyona özel eklenti sıralaması, OCR teklif rozetleri ve seçim güvenilir biçimde anlaşılamadığında elle onay.
- Stat Anvil parçası önerisi, Elixir zamanlaması ve elle seçilen Headliner için açıklamalar.
- Elixir of Iron / Sorcery / Wrath 500 altındır, 9. seviye gerektirir ve üç dakika sürer. Zamanlama altını, tamamlanmış eşyaları ve maç süresini hesaba katar; kurallar `ingame-app/elixir.py` içindedir.
- Görev çubuğunda görünen ana panel. `Ctrl+Alt+Z` veya `_` düğmesi paneli başlık çubuğuna daraltır; `X` uygulamayı kapatır. Elmas düğmesi panel konumunu sıfırlar.
- Göndermeden önce isteğe bağlı tanı bilgilerini inceleyebileceğin hata bildirim penceresi.

## Öneriler nereden geliyor?

Python motoru (`app.py`) mantığı ve OCR işlemlerini yürütür; Electron (`ui/`) motoru alt süreç olarak başlatır ve stdin/stdout üzerinden JSON alışverişi yapar. Koordinatlar fiziksel pikseldir, arayüz bunları monitöre göre dönüştürür. HUD çerçevesi oyun atlasından gelir; Beaufort/Spiegel yazı tipleri ilk kullanımda CommunityDragon'dan indirilir, yoksa sistem yazı tipleri kullanılır.

| Girdi | Kaynak ve kullanım |
| --- | --- |
| Mayhem eşya dizilimleri, sihirdar büyüleri, şampiyon ve eklenti/eşya istatistikleri | ARAMKit; `ingame-app/update_aramkit.py` tarafından hazırlanıp yerel JSON dosyalarında/paketlerinde saklanır. |
| Şampiyon seçimi tier listesi | `lcu-app/update_tier_list.py` aracılığıyla u.gg. |
| Şampiyon seçimi | Yerel League Client API (LCU); port ve kimlik bilgileri `LeagueClientUx.exe` süreç argümanlarından bulunur. |
| Oyuncular, envanterler, altın, seviye ve saldırı menzili | Riot Live Client Data API: `https://127.0.0.1:2999/liveclientdata`. |
| Sunulan eklentiler | Oyun penceresinin ilgili bölgelerinde Windows OCR. Seçim ayrıca gözlenen değişikliklerden çıkarılabilir veya elle onaylanabilir. |
| Eşya kuralları ve eklenti gereksinimleri | Yerel JSON yapılandırması ve Python kuralları. |
| Simgeler, dokular ve yazı tipleri | Riot Data Dragon / CommunityDragon; yazı tipleri gerektiğinde indirilir, yoksa sistem yazı tipleri kullanılır. |

Motor hazırlanmış şampiyon diziliminden başlar. Kullanılamayan eşyaları eler, eklenti gereksinimlerini öne alır; durumsal eşyaları karşı eşya kuralları, eklentiye bağlı kazanma oranları, desteklenen on-hit/crit tercihleri ve kaynak sırasıyla seçer. Her olası dizilimi optimize eden eğitilmiş bir model değildir; kural tabanlı öneri sistemidir. Birleştirilmiş istatistik açıklamaları katkı veren bütün eklentileri belirtir ve değerin koşullu istatistiklerin ortalaması olduğunu yazar. Bu değer, eklenti birleşiminin ölçülmüş kazanma oranı veya mevcut maçını kazanma ihtimalin değildir.

Yeni veri çıktıları, mevcut üç değerli istatistik satırlarını değiştirmeden örneklem sayılarını isteğe bağlı `augment_samples` haritasında korur. Sayılar varsa motor örneklem ağırlıklı ortalama kullanır; eski paketlerde eşit ağırlıklı ortalama korunur. Mevcut gömülü veri bu örneklem sayılarını içermiyor.

## Kurulum ve çalıştırma

### Bu çalışma kopyası

Burada anlatılan değişiklikler yerel geliştirmelerdir; yayımlanmış kurulum sürümü değildir. Kaynaktan çalıştırmak için:

1. Depoyu yazılabilir bir klasöre indir veya klonla.
2. `INSTALL.bat` dosyasını çalıştır. Eksik Python/Node.js için winget kurulumunu dener, `.venv` ve Electron bağımlılıklarını hazırlar, selfcheck çalıştırır ve masaüstü kısayolu oluşturur.
3. `START.bat` veya kısayolla aç. Gerekli çalışma zamanı dosyaları yoksa `START.bat` kurulum betiğini çağırır.

Kurulum betiği Python yorumlayıcı sürümünü sabitlemez. Çalışan bir `.venv` varsa koru. Bu bilgisayarda proje ortamı Codex çalışma zamanından gelen Python 3.12.14, PowerShell varsayılanı ise Python 3.14.6'dır. Ayrı `dist/quality-py314` ortamı uyumluluk testleri içindir. Yalnızca `.venv` yoksa mevcut Python 3.14 yorumlayıcısıyla oluştur. Depo kökünde PowerShell ile elle kurulum:

```powershell
if (-not (Test-Path .venv/Scripts/python.exe)) {
    py -3.14 -m venv .venv
}
.venv/Scripts/python.exe -m pip install -r requirements.txt
Push-Location ui
npm ci
node node_modules/electron/install.js
Pop-Location
./START.bat
```

Electron kurulum komutu, npm ilkesi onun kurulum betiğini atladıysa yararlıdır. Windows OCR için kullanılabilir İngilizce dil motoru gerekir. Kurulumun konsol mesajları hâlâ Romence olabilir.

### Orijinal projenin sürümleri

Orijinal projenin [sürümlerinde](https://github.com/CyberKird/aram-mayhem-helper/releases) `ARAM-Mayhem-Helper.exe` bulunur. Bu yükleyiciler burada belgelenen yerel değişiklikleri içermeyebilir. Paketlenmiş uygulama ayarları, günlükleri ve eşitlenen verileri `%APPDATA%/ARAM Mayhem Helper` altında saklar.

## Güncellemeler ve çevrimdışı kullanım

- Uygulama güncellemeleri hâlâ **CyberKird/aram-mayhem-helper** kaynağını kullanır. Yeni bir orijinal sürüm, yerel değişikliklerin üzerine kurulabilir. `--no-update`, o açılış için otomatik uygulama güncelleme kontrolünü atlar; veri eşitlemesini kapatmaz.
- `data_sync.py` başlangıçta ve 30 dakikada bir orijinal depodan tier, şampiyon istatistiği ve Mayhem veri paketini kontrol eder. Depodaki GitHub iş akışı ARAMKit verisi üretimini günlük zamanlar; güncellemenin gerçekleşmesi iş akışının başarıyla çalışmasına bağlıdır.
- İndirilen veri doğrulanır ve atomik yazılır; daha yeni yerel veri eski indirmeyle değiştirilmez. İndirme başarısızsa önceki kullanılabilir veri korunur.
- Dosyalar değiştiğinde build paketi yeniden okunur; oynanan şampiyonun dizilimi uygulama yeniden başlatılmadan yenilenebilir. Şampiyon tier/istatistik modülleri mevcut yaşam döngüsünü korur; bütün veri kaynakları canlı yenilenmez. Paket yaması, uygulamayla gelen katalog/kısıt yamasından farklıysa katalog tabanlı aday genişletme kapatılır.
- Gömülü/önbellekteki veriler çevrimdışı kullanılabilir. Yazı tipi indirme, yeni istatistikler, uygulama güncellemeleri ve hata bildirimi gönderimi internet gerektirir.

Bakımını yaptığın bir fork dağıtmadan önce kendi uygulama/veri güncelleme kanallarını yapılandır. Belgeleri değiştirmek bu adresleri değiştirmez.

## Doğrulama

Yerel kontrol araçlarını bir kez kur, ardından depo kökünde bütün kalite paketini çalıştır:

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-quality.txt
.\CHECK.bat
```

Bu komut proje yorumlayıcısıyla Ruff lint, Ruff biçim kontrolü, Pyright ve Pytest çalıştırır. Herhangi bir adım başarısızsa komut hata koduyla çıkar. Küçük değişiklik örneği: `.\CHECK.bat --files data_sync.py --tests test_data_sync.py`. Mevcut unittest testlerini Pytest de toplar. `AGENTS.md`, kod değişikliklerinden sonra ilgili kontrolleri, kapsamlı işi tamamlamadan önce bütün paketi zorunlu tutar. VS Code varsayılan yorumlayıcısı `.venv` oldu; iki yerel modül dizini de tanımlandı.

Proje ortamı Python 3.12.14. Ayrı bir Windows Python 3.14.6 ortamında da mevcut bağımlılıklarla bütün kalite paketi ve gerçek Windows OCR motorunu kullanan selfcheck geçti. Yorumlayıcı sürümü düşürülmedi ve mevcut ortam değiştirilmedi. VS Code'un kayıtlı yorumlayıcı seçiminin `.venv/Scripts/python.exe` olduğu doğrulandı; yalnızca varsayılan yol ayarı mevcut bir seçimi değiştirmez. Bu sonuç, minimum gereksinimlerin izin verdiği bütün eski paket sürümlerini doğrulamaz. Kapsam ve sınırlar: [kalite incelemesi](docs/quality-audit.md).

Depo kökünde PowerShell ile çalıştır:

```powershell
.venv/Scripts/python.exe -m unittest test_data_sync
.venv/Scripts/python.exe -m unittest discover -s ingame-app -p "test_*.py"
.venv/Scripts/python.exe app.py --selfcheck
```

Bu testler atomik güncelleme hatasını, bozuk/eski veriyi, canlı paket değişimini, yerel şampiyon kataloğunda altı eşya sınırını, şampiyonlar arası aday genişletme ve envanter senaryolarını, eşya grubu kısıtlarını, MR/zırh/can karşılıklarını, takım anti-heal kontrolünü, tam build satışlarını, hasar dönüşümünü, yığınlama/görev önceliğini ve istatistik açıklamalarını/uyumluluğunu kapsar. Selfcheck üretilmiş bir görüntü üzerinde gerçek Windows OCR motorunu da çalıştırır; simge/veri kapsamını kontrol eder ve açık maç gerektirmez.

Son yerel doğrulamada 41 Pytest testi (29 öneri ve 3 veri güncelleme testi dahil), 178 unittest alt testi, altı arayüz senaryosu ve rozet/bildirim kontrolleri geçti. Öneri matrisi 173 şampiyonu 1.038 rakip/envanter senaryosunda kapsıyor. Bunlar doğrulama sonuçlarıdır; her oyun durumu için garanti değildir. Güncellenen öneri motoru henüz canlı maçta doğrulanmadı.

Arayüz test verilerini üretip taklit motorunu çalıştırmak için:

```powershell
.venv/Scripts/python.exe ui/test/make_scenarios.py
$env:ARAM_MOCK = (Resolve-Path ui/test/game1080.json).Path
Push-Location ui
npx electron .
Pop-Location
Remove-Item Env:ARAM_MOCK
```

Taklit motoru hata bildirimi göndermez. Üretilen senaryo dosyaları geliştirme çıktısıdır.

## Verileri yeniden üretme

Bu komutlar üretilmiş JSON verilerinin üzerine yazar; oluşan değişiklikleri incele. Canlı maç dışında çalıştır.

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe ingame-app/update_aramkit.py
.venv/Scripts/python.exe ingame-app/build_icons.py
```

ARAMKit güncellemesi HTTP kullanır; tarayıcı gerektirmez. Ayrı u.gg şampiyon tier listesini güncellemek için Playwright kullanılır:

```powershell
.venv/Scripts/python.exe -m playwright install chromium
.venv/Scripts/python.exe lcu-app/update_tier_list.py
```

Depoda eski u.gg veri toplama araçları da bulunur. Güncel Mayhem eşya dizilimlerinin ana üretim yolu bunlar değildir. Klasik ARAM üreticisiyle Mayhem eşya verilerinin üzerine yanlışlıkla yazmamaya dikkat et.

## Windows uygulamasını derleme

Önce yukarıdaki kaynak testlerini çalıştır. Yayımlanacak sürüm için derlemeden önce `ui/package.json` sürümünü hedef sürümle eşleştir; yerel doğrulama derlemesi kendiliğinden sürüm yayımlamaz.

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe -m PyInstaller engine.spec --noconfirm --clean
dist/aram-engine/aram-engine.exe --selfcheck
Push-Location ui
npm ci
npx electron-builder --win nsis --publish never
Pop-Location
```

Bir komut başarısızsa sonraki adıma geçme. Motor `dist/aram-engine`, yükleyici `dist/ARAM-Mayhem-Helper.exe` altında oluşur. Spec, geliştirme çalışma zamanının ek SSL veri dosyasını varsa pakete alır. Bilerek yayımlanan otomatik güncelleme sürümünde yükleyici, `.blockmap` ve `latest.yml` aynı sürüme ve yapılandırılmış kanala ait olmalıdır.

## Sınırlar ve hata bildirimi

- OCR teklifleri kaçırabilir veya yanlış okuyabilir. İngilizce OCR ve üretilmiş test görüntüleri kontrol edildi; diğer istemci dilleri ve her çözünürlük için garanti verilmez.
- Eklenti seçimi, seçilen eklentiyi veren özel bir API'den okunmak yerine gözlenir/çıkarılır. Elle onay hâlâ önemlidir.
- Öneriler, hazırlanmış dizilimi aynı yamaya ait Mayhem mağaza kataloğundan uygun karşı eşyalarla genişletir. Build profili, mevcut/çekirdek eşya istatistiklerini ve desteklenen hasar dönüşümü eklentilerini izler. Bunlar elle yazılmış sezgisel kurallardır; her takım savaşını veya eklenti birleşimini simüle etmez.
- Eksik tier yerine uydurma sıralama gösterilmez. Kamuya açık veri kapsamı ve güncelliği sistemi sınırlar.
- Hata bildirim düğmesi böcek simgesidir. Bildirimler hâlâ FormSubmit üzerinden orijinal geliştiricinin `contact@joltarise.com` adresine gider. E-posta isteğe bağlıdır; tanı bilgileri gönderimden önce incelenebilir ve gönderim başarısızsa e-posta alternatifi sunulur. Bildirim kodu ekran görüntüsü eklemez.
- Ana pencere odak alabilir; küçük oyun üstü rozetleri odak almaz.

## Proje yapısı

```text
app.py                         Motor giriş noktası ve JSON durum protokolü
bug_report.py                  Bildirim doğrulama, tanı ve gönderim
data_sync.py                   Atomik veri indirme ve sürüm kontrolü
engine.spec                    PyInstaller motor paketlemesi
ui/main.js                     Electron pencereleri, konum ve güncelleyici
ui/renderer/                   Ana panel, rozetler, ipuçları ve bildirim arayüzü
ui/test/                       Taklit motoru ve senaryo üreticisi
lcu-app/                       LCU erişimi ve şampiyon seçimi verileri
ingame-app/live_client.py       Canlı maç verisine erişim
ingame-app/decision_trace.py    Yerel karar kaydı ve çevrimdışı tekrar
ingame-app/item_costs.py        Gözlemsel eşya tamamlama maliyeti karşılaştırması
ingame-app/rules_engine.py      Eşya seçimi, satın alma ve satış kuralları
ingame-app/bundle.py            Doğrulanmış build paketi önbelleği ve yenileme
ingame-app/update_aramkit.py    Güncel Mayhem veri üreticisi
ingame-app/test_recommendations.py  Motor ve paket regresyon testleri
ingame-app/test_item_costs.py    Tarif ve maliyet karşılaştırması regresyon testleri
test_data_sync.py              İndirme/yazma regresyon testleri
test_decision_evidence.py      Kurtarma, kayıt ve tekrar regresyon testleri
overwolf-app/                  Tarihsel alternatif uygulama
```

Etkin masaüstü giriş noktası kökteki `app.py` ve `ui/` dizinidir.

## Yerel karar kaydı ve bağlantı kurtarma

Kaynak motor, kısa Live Client API kesintilerinde son durumu korur. Başarısız okuma hemen belirtilir, veri yokken öneri yeniden hesaplanmaz ve son başarılı kadro okumasından 12 saniye sonra satın alma önerileri gizlenir. Veri 30 saniyedir yoksa ve oyun penceresi de bulunamıyorsa oturum sıfırlanır. Oyun saatinin geriye dönmesi de önceki maçın seçimlerini temizler. Bunlar kurtarma eşikleridir; güncellemenin kesinlikle dört saniyede tamamlanacağı anlamına gelmez.

Karar veya arayüze gönderilen satın alma önerisi değiştiğinde masaüstü motoru `%APPDATA%/ARAM Mayhem Helper/decision-logs` altında (veya `ARAM_HOME/decision-logs`) yerel JSONL kaydı tutar. Python motoru doğrudan çalıştırılırsa varsayılan konum proje kökündeki `decision-logs` klasörüdür. Her kayıt, hesaplamada kullanılan girdileri/verileri, seçilmiş augmentleri, oyun zamanını, sonucu, karar/oturum kimliğini ve stdout üzerinden gönderilen eşya planını içerir. Oyuncunun Riot ID'si ve LCU kimlik bilgileri kaydedilmez. Kayıt, motorun gönderimini kanıtlar; ekranda çizildiğini kanıtlamaz.

Disk yazımı sınırlı bir arka plan kuyruğunda yapılır. En fazla dört adet 8 MiB dosya tutulur; kuyruk taşması/yazma hatası stderr ve panel durumunda bildirilir. Beklenmedik kapanış son satırı yarım bırakabilir. Çevrimdışı tekrar, bozuk satırları ve öneri farklarını sıfırdan farklı çıkış koduyla bildirir; kaydedilen verileri mevcut hesaplama motoruyla kullanır, oyun/API isteği yapmaz:

```powershell
.venv/Scripts/python.exe ingame-app/decision_trace.py "$env:APPDATA/ARAM Mayhem Helper/decision-logs/decisions.jsonl"
```

Bu özellik güncel kaynak motoru (`START.bat`) veya yeniden derlenmiş motoru gerektirir. Geliştirme bilgisayarında mevcut masaüstü simgesi artık bu projenin Electron uygulamasını ve `.venv` motorunu `--no-update` ile açar; sonraki doğrulanmış kaynak değişiklikleri, batch dosyası çalıştırmadan veya yeniden kurmadan bir sonraki açılışta kullanılır. Zaten çalışan uygulamanın oyun dışında yeniden açılması gerekir. Eski kısayol `dist/backup-desktop-source-2026-10-28` altında yedeklidir; kurulu uygulama dosyaları korunur. Bu yerel bir ayardır, GitHub otomatik güncelleme kanalı değildir. Kayıtlar sınırlı tanılama kanıtıdır; eksiksiz satın alma geçmişi veya en iyi öneri garantisi değildir.

Karar kayıtları artık sürümlü `extra.live_context` alanını da taşır: güncel yanıttaki seviye/altın, belgelenmiş sayısal yerel şampiyon istatistikleri ve eşya ID'si, slotu, adedi korunan anonim oyuncu envanterleri. Eksik tekil değerler `null`, eksik istatistik alanları atlanmış, alınamayan envanterler `null` olur; sıfır gerçek gözlemlenen değerdir. Sıra numaraları kalıcı oyuncu kimliği değildir. Mevcut sıralama bu gözlemsel bağlamı kullanmaz; eski şema-1 kayıtları da tekrar oynatılır. Rakibin ayrıntılı şampiyon istatistikleri tahmin edilmez; ayrı API yanıtları aynı ana ait atomik bir görüntü değildir. İstatistikler değiştikçe kayıt sıklığı artabilir; saklama sınırı korunur. Çalışan uygulama bu değişikliği oyun dışında yeniden açıldığında yükler.

Veri kullanım denetimi ve doğrulanan Mayhem açıklaması, altın ayrıştırma ve mana etiketi düzeltmeleri [teknik raporda](docs/recommendation-data-audit.md) açıklanıyor. Bu düzeltmeler yeni bir eşya sıralama modeli getirmiyor.

Tarif içeren kayıtlara isteğe bağlı `cost_comparison` eklenir: tam nominal fiyat, eldeki bileşen kredisi, kalan maliyet ve gözlemlenen altına göre eksik tutar. Alternatifler bağımsız hesaplanır; en ucuz tamamlama öneri sırasını değiştirmez. Eksik, döngüsel, doğrulanmamış veya yaması uyuşmayan tariflerde bedava eşya varsaymak yerine maliyet bilinmiyor olarak kaydedilir. Tekrar oynatma, alan varsa onu da doğrular; eski kayıtlar uyumludur. İndirimler, mağaza erişimi ve satın alma için slot uygunluğu simüle edilmez.

## Atıf ve lisans

Orijinal geliştirici: **Joltarise / CyberKird**. [Orijinal proje](https://github.com/CyberKird/aram-mayhem-helper) · [Orijinal geliştiriciyi destekle](https://ko-fi.com/joltarise).

[LICENSE](LICENSE) dosyası GNU GPL sürüm 3 metnini içerir; orijinal README GPL-3.0-or-later beyan ediyordu. `ui/package.json` içindeki lisans alanı şu anda `UNLICENSED` olduğundan paket metaverisi ile orijinal lisans beyanı uyumlu değil. Bu belge güncellemesi lisansı veya eser sahipliğini değiştirmez. Üçüncü taraf istatistikleri, yazı tipleri ve oyun varlıkları sahiplerinin koşullarına tabidir.

Proje gayriresmîdir; Riot Games ile bağlantılı değildir ve Riot tarafından onaylandığı iddia edilmez. Türev ürün dağıtmadan önce [Riot geliştirici belgeleri ve politikalarını](https://developer.riotgames.com/docs/lol) incele.
