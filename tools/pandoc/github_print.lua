local stringify = pandoc.utils.stringify

local function trim(s)
  return (s:gsub("^%s+", ""):gsub("%s+$", ""))
end

local function starts_with(str, prefix)
  return str:sub(1, #prefix) == prefix
end

local function normalize_local_path(src)
  if starts_with(src, "http://") or starts_with(src, "https://") or starts_with(src, "data:") then
    return src
  end

  while starts_with(src, "./") do
    src = src:sub(3)
  end

  while starts_with(src, "../") do
    src = src:sub(4)
  end

  return src
end

local admonition_titles = {
  NOTE = "Note",
  TIP = "Tip",
  IMPORTANT = "Important",
  WARNING = "Warning",
  CAUTION = "Caution",
}

local function parse_admonition_marker(block)
  if block.t ~= "Para" and block.t ~= "Plain" then
    return nil
  end

  local text = trim(stringify(block))
  local kind = text:match("^%[!(%u+)%]$")
  if not kind or not admonition_titles[kind] then
    return nil
  end

  return kind
end

function BlockQuote(el)
  if #el.content == 0 then
    return nil
  end

  local kind = parse_admonition_marker(el.content[1])
  if not kind then
    return nil
  end

  local content = {}
  table.insert(
    content,
    pandoc.Div(
      { pandoc.Para({ pandoc.Str(admonition_titles[kind]) }) },
      pandoc.Attr("", { "admonition-title" })
    )
  )

  for i = 2, #el.content do
    table.insert(content, el.content[i])
  end

  return pandoc.Div(content, pandoc.Attr("", { "admonition", "admonition-" .. string.lower(kind) }))
end

function CodeBlock(el)
  if el.classes:includes("mermaid") then
    return pandoc.RawBlock("html", '<pre class="mermaid">' .. el.text .. "</pre>")
  end

  if el.classes:includes("math") then
    return {
      pandoc.RawBlock("html", "$$"),
      pandoc.Plain({ pandoc.Str(el.text) }),
      pandoc.RawBlock("html", "$$"),
    }
  end

  return nil
end

function Image(el)
  el.src = normalize_local_path(el.src or "")
  return el
end

function RawInline(el)
  if el.format ~= "html" then
    return nil
  end

  local rewritten = el.text:gsub('src="([^"]+)"', function(src)
    return 'src="' .. normalize_local_path(src) .. '"'
  end)

  if rewritten ~= el.text then
    return pandoc.RawInline("html", rewritten)
  end

  return nil
end

function RawBlock(el)
  if el.format ~= "html" then
    return nil
  end

  local rewritten = el.text:gsub('src="([^"]+)"', function(src)
    return 'src="' .. normalize_local_path(src) .. '"'
  end)

  if rewritten ~= el.text then
    return pandoc.RawBlock("html", rewritten)
  end

  return nil
end
