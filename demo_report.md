# Rapor Yazma Rehberi — Game Console OS

Toplam 5-6 sayfa. Aşağıdaki sırayla yaz, her bölüm için ne kadar yazman gerektiğini belirttim.
Kod ekrana görüntü olarak koyma. En az bir mimari diyagram ve bir akış diyagramı zorunlu.

---

## 1. System Overview & Theme
*Yarım sayfa*

Projenin ne olduğunu anlat. Game Console OS seçtiğini ve bunun bir simülasyon olduğunu belirt.
Neden bu temayı seçtiğinizi açıkla — tasarım kararları doğal olarak gerekçeleniyor,
RAM kısıtlı, tüm process'lerin yanıt vermesi gerekiyor gibi.

Simüle ettiğin 4 process'i say: GameEngine, AudioManager, InputHandler, SaveManager.
Neden Python seçtiğini bir cümleyle yaz.

Sayıları buraya ekle: `config.py` dosyasına bak — RAM_FRAMES, TIME_QUANTUM, MAX_PROCESSES.

---

## 2. Architecture Diagram
*Bir diyagram + 3-4 cümle*

Diyagramı draw.io ya da Excalidraw ile çiz, PNG olarak ekle. Elle de çizebilirsin.

Diyagramda şu yapı olmalı — kutular ve oklar:

```
[ GameEngine ]  [ AudioManager ]  [ InputHandler ]  [ SaveManager ]
                          |
                    [ Scheduler ]
                    /            \
         [ Memory Manager ]    [ File System ]
                                      |
                               [ Concurrency ]
```

Açıklama cümlelerinde şunları söyle: Scheduler merkezi koordinatör,
Memory Manager frame dağıtıyor, File System lock için Concurrency modülünü kullanıyor,
process bloklandığında Scheduler'a haber gidiyor.

---

## 3. Key Design Decisions & Alternatives
*Bir buçuk sayfa — en önemli bölüm bu*

Her karar için şu dört satırı yaz. Hoca bunları görmek istiyor.

```
Seçilen:          ...
Düşünülen:        ...
Neden reddettik:  ...
Kabul ettiğimiz:  ...
```

Dört karar yazman gerekiyor:

---

**Scheduler — Round Robin**

`scheduler.py` dosyasının başına bak, design justification comment'ları orada.
TIME_QUANTUM = 3 olduğunu yaz.
Alternatif olarak MLFQ'yu düşündüğünüzü ama 4 process için gereksiz karmaşıklık
getireceği için reddettiğinizi açıkla.
Kabul ettiğin trade-off: context switch overhead artıyor ama her process eşit CPU alıyor.

---

**Memory — Fixed Frame Paging**

`memory_manager.py` dosyasına bak.
RAM_FRAMES = 16, her process sabit sayıda frame alıyor.
Alternatif segmentation'dı — değişken boyutlu bölgeler ve dış parçalanma sorunu
getireceği için reddettik.
Kabul ettiğin trade-off: iç parçalanma olabilir ama adres çevirisi basit kalıyor.

---

**Concurrency — SimpleLock**

`concurrency.py` dosyasına bak.
Binary mutex seçildi çünkü file system'de tek yazıcı yeterli.
Alternatif semaphore'du — sayıcılı erişim gerekmiyor.
Kabul ettiğin trade-off: eş zamanlı okuma desteği yok ama gereksiz karmaşıklıktan kaçınıldı.

---

**File System — In-Memory Dictionary**

`file_system.py` dosyasına bak.
Dosyalar Python dictionary'de tutuluyor, disk yok.
Alternatif gerçek disk I/O'ydu — simülasyonu bozardı çünkü gerçek OS gecikmeleri
scheduler davranışını gizlerdi.
Kabul ettiğin trade-off: kalıcılık yok, program kapanınca dosyalar siliniyor.

---

## 4. Cross-Component Interactions
*Üç çeyrek sayfa + bir sequence diyagramı*

İki etkileşim açıklanacak.

---

**Etkileşim 1 — Memory → Scheduler**

Bir process yeterli frame bulamazsa ne oluyor adım adım yaz:
`memory_manager.py` → `allocate()` False döner →
`handle_exhaustion()` çağrılır →
`process_manager.block_process()` state'i "blocked" yapar →
Scheduler process'i queue'dan çıkarır.

Bunu bir sequence diyagramı olarak çiz: Process → MemoryManager → ProcessManager → Scheduler

---

**Etkileşim 2 — File Lock → Scheduler**

SaveManager file yazmak istiyor, lock başka process'te:
`file_system.py` → `write_file()` lock almaya çalışır →
Alamazsa `scheduler.handle_blocked()` çağrılır →
Process "blocked" olur, queue'dan çıkar →
Lock release olunca `unblock_process()` ile "ready"'e döner.

`file_system.py` içindeki `write_file()` metoduna ve `main.py` deadlock demo bölümüne bak.

---

## 5. Engineering Challenge & Failure Scenario
*Bir sayfa*

---

**Deadlock Detection**

Neden oluştuğunu açıkla: SaveManager FileSystem lock'u tutuyor ve MemoryBus'ı bekliyor.
GameEngine MemoryBus'ı tutuyor ve FileSystem'i bekliyor. İkisi birbirini bekliyor, çıkış yok.

Nasıl yakaladığınızı açıkla: `concurrency.py` içindeki `DeadlockDetector` sınıfına bak.
hold_graph kimin neyi tuttuğunu, wait_graph kimin neyi beklediğini takip ediyor.
`detect()` metodu döngü var mı kontrol ediyor.

Nasıl çözdüğünüzü açıkla: En düşük priority'li process sonlandırılıyor.
Lock release ediliyor, diğer process devam ediyor.

Terminal çıktısından şu bölümü rapora al — "Engineering Challenge" section'ından kopyala:
```
uv run python main.py
```
"DEADLOCK DEMO" başlığının altındaki log satırlarını ekle.

Sınırlılıklarını dürüstçe yaz: Detector sadece iki process arasındaki döngüyü buluyor.
Üç process'li deadlock yakalanmıyor. Sonlandırma kararı her zaman optimal değil.

---

**Memory Exhaustion**

`config.py` dosyasında `FORCE_MEMORY_EXHAUSTION = True` yap ve çalıştır.
Çıktıdan EXHAUSTION log satırlarını rapora al.

Ne olduğunu yaz: Process blocked state'e geçiyor, sistem çalışmaya devam ediyor.
Bu davranış kabul edilebilir mi: Evet, sistem çökmüyor.

---

## 6. Baseline vs Enhanced Comparison
*Yarım sayfa + tablo*

`uv run python main.py` çalıştır, "Scheduler Comparison" bölümündeki tabloyu rapora al.
Tabloyu elle yaz ya da screenshot yerine Word/Google Docs'ta oluştur.

Tablo altına şunu yaz: FIFO'da turnaround daha kısa çünkü ilk gelen process
bitmeden diğeri başlamıyor. RR'da first response time çok daha iyi —
ortalama 4.5 vs 11.5 tick. Game console'da InputHandler ve AudioManager
gecikmeden CPU almalı, bu yüzden turnaround'u feda edip RR seçildi.

---

## 7. Limitations & Future Improvements
*Yarım sayfa*

Kısıtlamaları dürüstçe yaz, uzatma:

- File system kalıcı değil, her çalıştırmada sıfırlanıyor
- Deadlock detector sadece iki process arasındaki döngüyü buluyor
- Bellek dolunca blocked process'i otomatik kurtaran mekanizma yok
- Tick tabanlı simülasyon gerçek zaman değil

İlerisi için ne yapılabilirdi:
- Priority'e göre değişken time quantum
- Üç ve daha fazla process'li deadlock tespiti
- Starvation önleme için process aging

---

## Diyagram için

draw.io → https://draw.io
Excalidraw → https://excalidraw.com

Mimari diyagram için kutular ve oklar yeterli, renk şart değil.
Sequence diyagram için soldan sağa, her adım numaralı olsun.