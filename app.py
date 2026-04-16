def parse_ar_fallback(file):
    records = []

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""

            text = normalize(text)

            # استخراج رقم الموبايل
            phone_match = re.search(r'(01[0125]\d{8})', text)

            if not phone_match:
                continue

            phone = phone_match.group(1)

            numbers = extract_numbers(text)

            # حماية من تكرار رقم الموبايل داخل الأرقام
            numbers = [n for n in numbers if str(int(n)) != phone]

            def g(i): return numbers[i] if i < len(numbers) else 0

            records.append({
                "محمول": phone,
                "رسوم شهرية": g(0),
                "رسوم الخدمات": g(1),
                "مكالمات محلية": g(2),
                "رسائل محلية": g(3),
                "إنترنت محلية": g(4),
                "مكالمات دولية": g(5),
                "رسائل دولية": g(6),
                "مكالمات تجوال": g(7),
                "رسائل تجوال": g(8),
                "إنترنت تجوال": g(9),
                "رسوم تسويات": g(10),
                "ضرائب": g(11),
                "إجمالي": g(-1),
            })

    return records
