# Öneri verisi ve kullanım denetimi — 2026-10-28

Denetim, mevcut Electron/Python motorunu ve 16.21 Mayhem verilerini kapsar. Yeni bir profil sistemi veya eşya puanlama modeli eklenmedi. Veri bütünlüğü, verinin motorda kullanılması ve önerinin oyun içindeki değeri ayrı değerlendirildi.

## Doğrulanan kapsam

- Git tarafından izlenen 378 JSON dosyası ayrıştırıldı: sözdizimi hatası ve tekrar eden nesne anahtarı yok.
- 173 build'in şampiyon etiketleri ve menzil kayıtları mevcut. Başlangıç/core/alternatif/pool eşya referanslarında, motorun ad normalizasyonuyla tanınmayan eşya yok.
- Mayhem bundle ve eşya kataloğu 16.21. Katalogda 197 eşya, tariflerde 197 kayıt, eşya özelliklerinde 170 ve özel gruplarda 148 kayıt var. Bu sayılar dosyaların farklı görevlerini yansıtır; hepsinin aynı sayıda olması beklenmez.
- Bunlar mağazada bütün eşyaların fiilen satın alınabildiğini veya bütün pasiflerin doğru modellendiğini kanıtlamaz.

## Veri nerede kullanılıyor?

| Veri | Mevcut kullanım | Karar kalitesi açısından sınır |
| --- | --- | --- |
| 173 şampiyonun hasar türü/sınıfı | `item_candidates.profile`, karşı eşya kuralları, Anvil ve Elixir | Yetenek oranları, pasif tetikleme biçimleri ve savaş rotasyonu yok. |
| 173 şampiyonun Mayhem build'i | Core/alternatif sırası, augment istatistikleriyle seçim | Kaynak oyuncu istatistikleri şampiyon mekaniğini dolaylı yansıtır; belirli durum için nedensel karşılaştırma değildir. |
| Temel ve canlı menzil | `rules_engine.current_range` ile eşya uygunluğu | Kayle kaydında 175 → 525 ve melee → ranged geçişi doğrulandı. Tam seviye mekanik modeli değildir. |
| Eşya kataloğu | Mağaza uygunluğu; AP/AD/tank uyumu; basit on-hit/crit tercihi | Saldırı hızı, haste, mana ve pasiflerin marjinal faydası birlikte hesaplanmıyor. |
| Eşya tarifleri ve fiyat | `_build_cost` / `remaining_gold`, Anvil/Elixir rezervi | Rakibe karşı eşya seçerken mevcut bileşenlerin fırsat maliyetini karşılaştırmıyor. |
| Canlı seviye ve altın | OCR etkinliği, seçim çıkarımı, Anvil/Elixir; sonraki bağlam paketinde `extra.live_context` ile kayıt | Bağlam artık taşınıyor; eşya sıralaması henüz seviye/altını karşılaştırmada kullanmıyor. Canlı menzil mevcut uygunluk kararında kullanılıyor. |
| Rakip envanterleri | HP/armor/MR/heal özelliği taşıyan eşya sayısı; sonraki bağlam paketinde anonim oyuncu envanterleri de korunuyor | Eski karşı eşya kuralları hâlâ düz listeyi kullanıyor. Eşya sayısı, ayrı tehdit sayısı veya kesin toplam direnç değildir. |
| Mayhem denge verisi | 105 şampiyonda değiştirici, 49 şampiyonda yetenek değişikliği; arayüz açıklaması | `champ_stats.info/balance` görüntüler; eşya resolver'ı bu veriyi tüketmez. Yüzdeleri bütün hasara körlemesine uygulamak güvenli bir çözüm değildir. |
| Özel augment etkileri | 48 kural; 44'ü mevcut OCR sözlüğünde. Damage/range dönüşümü, quest, stacking ve basit tercih | Dört kayıt kaldırılmış isimler için kalıntıdır; otomatik silinmedi. Tablo kapsamlı mekanik simülasyonu değildir. |
| Augment–eşya istatistikleri | 173 şampiyonda koşullu istatistik; birden çok augmentte ortalama | Mevcut bundle'da `augment_samples` yok; örneklem ağırlıklı güven ölçüsü kurulamaz. |
| Sekiz Headliner açıklaması | Kullanıcının seçimi ve metin gösterimi | Seçim `resolve_build` girdisine aktarılmıyor. Pentakill/HEAVY mekanik değerlemesi yok. |

## Kaynakla doğrulanan ve düzeltilen kusurlar

1. `augment-desc.json` güncelleyici tarafından Mayhem kaynağından yenilenmiyordu. Mad Scientist'in eski açıklaması tur başlangıcını söylüyordu; seçili Mayhem kaynağı yeniden doğuşu söylüyor. Warlock Juicebox dahil beş mevcut kaynak açıklaması eksikti. Güncelleyici artık kaynakta dolu açıklaması olan tam eşleşen isimleri yeniliyor, diğer isimleri fallback olarak koruyor.
2. Warlock Juicebox gibi açıklamalarda AP simgesi atılınca ölçeklemenin anlamı kayboluyordu. Metne çevirmede simge etiketleri köşeli parantezle korunuyor; bunlar hesaplanmış sonuç değil, kaynak etiketleridir.
3. Altın algılaması ilk `N Gold` ifadesini okuyordu. Collector'ın pasif 50 altını, seçim anındaki 250 altınla karışabiliyordu. Artık açık `Gain … Gold` ifadesi okunuyor; simge etiketi ve `Gain500` biçimi destekleniyor. Pasif ödül tek başına seçim kanıtı sayılmıyor.
4. Katalog `Mana` etiketini bekliyordu; aynı kaynak `Max Mana` kullanıyor. Yirmi eşyanın mana değeri atlanıyordu. Etiket eşleştirmesi düzeltildi; diğer istatistikler ve katalog sırası korundu.

Güncelleyicide açıklama ile mekanik kuralın kapsamı da ayrıldı: yeni kaynak metninde belirtilmeyen mevcut quest/birleşme/on-hit alanları, yalnızca açıklama kısaldı diye silinmiyor. Mevcut mekanik dosyası uyumluluk tabanı olarak kullanılıyor; korunması gereken çıkarım boşlukları `manual review` uyarısıyla listeleniyor. Bu koruma, eski mekaniklerin doğruluğunu kanıtlamaz; sessizce silinmelerini önler. Mevcut `augment-effects.json` değiştirilmedi.

Açıklamalar 417'den 422'ye çıktı: 222 mevcut metin yenilendi, beş metin eklendi. Seçili kaynağın 235 isminin tamamında açıklama var. 536 isimlik geniş OCR/fallback sözlüğünün 393'ünde açıklama var; kalan 143 ismi otomatik olarak eksik Mayhem mekaniği saymak doğru değil. Sözlük, seçili kaynaktan daha geniştir.

Kaynaklar: [16.21 Mayhem augment kaynağı](https://data.aramkit.com/resources/16.21-32001640c0a4/en-US/resources/augments.json), [aynı sürümün eşya kaynağı](https://data.aramkit.com/resources/16.21-32001640c0a4/en-US/resources/items.json). Ham kaynak ve önceki iki veri dosyası bu makinede ignored `dist/` altında saklandı. Tam güncelleyici çalıştırılmadı; build/tier/öneri istatistikleri yeniden indirilmedi.

## Sonraki uygulama sırası

1. Yetenek/pasif bilgisi eklemeden önce kaynak ve yama izini tutarlı kıl: `champion_ranges()` ve özel eşya grubu üreticisi halen `latest` kullanıyor. Bu, bugün yanlış olduklarının kanıtı değil; farklı yama verilerinin karışma riskidir.
2. Tamamlanan gözlemsel bağlam paketi: resolver'a isteğe bağlı seviye, altın, sayısal yerel şampiyon istatistikleri ve anonim oyuncu envanterleri `extra.live_context` ile aktarılıyor. İlk aşamada kayıt için taşınıyor; puanlamada kullanılmıyor. Plan ve doğrulama: [canlı karar bağlamı](superpowers/plans/2026-10-28-live-decision-context.md).
3. Ortak mekanik özellikleri mevcut profillere kaynak ve yama bilgisiyle ekle. Her değişiklik için hedeflenen bir karşılaştırma senaryosu tanımla; bütün şampiyonlar için el yordamıyla katsayı uydurma.
4. Aday karşılaştırmasını mevcut bileşen/maliyet, şampiyon–eşya etkileşimi ve rakip ihtiyacıyla genişlet. Önce kayıtlarda mevcut motorla yan yana çalıştır; gerekçeli iyileşme kanıtı olmadan canlı sıralamaya geçirme.

Kayle maçındaki 86 kayıt, mana alanı eklenmiş katalogla yeniden hesaplandı: eşya planında sıfır fark. Bu, sıralamanın korunduğuna ilişkin regresyon kanıtıdır; önerilerin optimal olduğunu kanıtlamaz. Canlı maç kesilmedi veya uygulama yeniden başlatılmadı. Yeni açıklamalar kaynak uygulamanın sonraki açılışında yüklenir.

Veri denetimi paketinin doğrulaması: Ruff lint/format temiz, Pyright sıfır hata/uyarı, 64 test ve 178 alt test başarılı. Kaynak selfcheck ve üç dilde README tutarlılık kontrolü geçti. Bağımsız incelemede bulunan mekanik alan kaybı riski regresyon testiyle giderildi; gerçek kaynakla tekrar üretimde mevcut alan kaybı veya değer değişikliği kalmadı. Paketli uygulama veri denetimi sırasında yeniden üretilmedi; masaüstü kısayolu kaynak motorunu kullanır.

## Bileşen maliyeti karşılaştırması

Sonraki paket, mevcut planın henüz alınmamış hedeflerini `cost_comparison` alanında bağımsız nominal maliyet alternatifleri olarak hesaplar. Ortak bileşen aynı hedef tarifinde iki kez tüketilmez; farklı alternatiflerin kredileri birbirine eklenmez. Aynı bitmiş eşyanın eldeki kopyası, ilave stackable kopyayı bedava yapmaz. Farklı bir yükseltmenin gerçek bileşeni olan bitmiş eşya ise kullanılabilir. Bu karşılaştırma canlı sıralamayı, quest önceliklerini veya satış önerilerini değiştirmez.

Kayle'nin 86 kaydında 398 hedef maliyeti hesaplandı ve yeni maliyet alanıyla tekrar oynatmada sıfır fark görüldü. 07:06 civarında Dagger ve Glowing Mote ile Dusk and Dawn 2.600, Liandry 3.000 altın gerektiriyor. 07:54 civarında Fated Ashes alındığında Liandry'nin kalanı 2.100 oluyor ve en düşük tamamlama maliyeti değişiyor. Eski kayıtlarda cüzdan bilgisi yoktu; altının yettiği veya yetmediği uydurulmadı. Bunlar fiyat karşılaştırmasıdır, stratejik üstünlük kanıtı değildir.

Kaynak güncelleyici artık eksik fiyatı/bileşeni veya aynı isimde çelişen tarifleri uyarıyla `cost_status=unverified` olarak işaretler. Yeni karşılaştırma bu tariflere kesin fiyat vermez. Legacy `gold/from` tahminleri eski Anvil/Elixir tüketicilerinin davranışını değiştirmemek için korunur; bu eski tahminler doğrulanmış fiyat garantisi değildir. Aynı ham kaynakta mevcut 197 tarif birebir aynı üretildi. Aktif fiyat dosyası değiştirilmedi. İndirimler, mağazada erişim ve slot uygunluğu bu paketin dışında; yama bilgisi eksikse tarifin yamaya uygunluğu ayrıca kanıtlanmış sayılmaz.

Maliyet paketinin doğrulaması: Ruff lint/format temiz, Pyright 1.1.414 sıfır hata/uyarı, 93 test ve 178 alt test geçti. Kaynak ve paketlenmiş motor selfcheck'leri, PyInstaller derlemesi, pip check, README tutarlılığı ve diff kontrolü başarılı. Canlı öneri sırası korunuyor; yeni kayıt alanının gerçek maçta yakalanması henüz doğrulanmadı. [Uygulama ve doğrulama notları](superpowers/plans/2026-10-28-item-cost-comparison.md).
