def clean_kurasel_text(note_text):
    return [line.strip() for line in note_text.splitlines() if line.strip()]


def clean_amount_str(value):
    return value.replace("¥", "").replace("（円）", "").replace(",", "").strip()


def parse_records_by_lines(lines, rows_per_record):
    """指定された行数ごとにリストを分割する汎用関数"""
    records = []
    for i in range(0, len(lines), rows_per_record):
        chunk = lines[i : i + rows_per_record]
        if len(chunk) == rows_per_record:
            # ¥やカンマをクリーンアップ
            clean_chunk = [
                item.replace("¥", "").replace("（円）", "").replace(",", "").strip() for item in chunk
            ]
            records.append(clean_chunk)
    return records
