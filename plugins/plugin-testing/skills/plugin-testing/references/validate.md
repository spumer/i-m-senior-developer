# Структурная проверка плагина

Бесплатная и детерминированная. Годится для каждого коммита и для CI.

## Полный набор вызовов

Корень плагина проверяет преимущественно манифест. Frontmatter компонентов
проверяется только при отдельной передаче каталогов:

```bash
claude plugin validate <plugin> --strict
claude plugin validate <plugin>/commands --strict
claude plugin validate <plugin>/skills --strict
claude plugin validate <plugin>/agents --strict
```

Маркетплейс проверяется своим манифестом:

```bash
claude plugin validate .claude-plugin/marketplace.json --strict
```

## Обнаружение без ручного списка

```bash
for manifest in plugins/*/.claude-plugin/plugin.json; do
  plugin=${manifest%/.claude-plugin/plugin.json}
  claude plugin validate "$plugin" --strict
  for components in commands skills agents; do
    [ ! -d "$plugin/$components" ] || claude plugin validate "$plugin/$components" --strict
  done
done
```

Ручной перечень плагинов в CI устаревает молча: новый плагин не попадёт под
проверку. Обнаружение по манифестам этой ошибки не допускает.

## Почему `--strict` обязателен

Без него часть проблем остаётся предупреждением, а код выхода равен `0`.
Измеренный пример: отсутствующий `description` у скилла без `--strict` даёт код
`0`, со `--strict` — код `1`.

## Измеренная граница

Неизвестное поле во frontmatter команды не отклоняется даже со `--strict`, хотя
описание флага обещает отказ на нераспознанных полях. Проверять договор команд
этой командой нельзя — нужен собственный тест на состав полей.

Граница установлена мутацией временной копии: добавление неизвестного поля не
изменило результат, удаление `description` у скилла изменило.

## Чего структурная проверка не делает

Она читает состав и схемы, а не результат работы. Плагин может пройти проверку и
быть бесполезным: описание корректно, файлы разбираются, но скилл никогда не
срабатывает на живом запросе. Это ловит только поведенческая проверка.

## Проверка манифестов как ранний отказ

Разбор JSON всех манифестов до вызова CLI даёт быстрый и дешёвый отказ на
опечатке:

```bash
for f in $(find plugins -path '*/.claude-plugin/plugin.json') .claude-plugin/marketplace.json; do
  python3 -c "import json,sys; json.load(open('$f'))"
done
```

## Установка CLI в CI

Проверка требует CLI, но не требует авторизации и модели. Версию закреплять
явно, иначе обновление зависимости меняет поведение проверки незаметно:

```yaml
- uses: actions/setup-node@v4
  with:
    node-version: "20"
- run: |
    npm install --global @anthropic-ai/claude-code@<version>
    test "$(claude --version | cut -d' ' -f1)" = "<version>"
```

Автообновление CLI в job отключать переменной `DISABLE_UPDATES=1`, чтобы
закреплённая версия не менялась во время прогона.
