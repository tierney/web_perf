require('hash')
require('ggplot2')
library(gridExtra)

PATH = '/home/tierney/repos/web_perf/empirical/2012_03_23_18_06_19/'

plot_convos = function(filename) {
  FLOWTIME = '/home/tierney/repos/web_perf/analysis/flowtime.rb'

  if (file.info(filename)[["size"]] == 0) {
    return()
  }

  data = read.csv(pipe(paste(FLOWTIME, filename)), header=T, sep=",")

  p = ggplot(data=data, aes(frame.time_relative, stream_id, color=direction)) +
    geom_point(aes(size = frame.len),
               position=position_jitter(width=0, height=0.2)) +
    scale_shape() +
    scale_x_continuous() +
    scale_color_hue() +
    opts(title = basename(filename))
  #out_svg = paste(filename, 'svg', sep='.')
  #ggsave(out_svg)
  return(p)
}

## p1 = plot_convos('/tmp/test.pcap')
## p2 = plot_convos('/tmp/tmobile.ff.pcap')

## show(grid.arrange(p1, p2))

## for (filename in list.files(PATH, pattern='(firefox|chrome).*.pcap$')) {
##  file_path = paste(PATH, filename, sep='')
##  plot_convos(file_path)
## }

h = hash()
for (filename in list.files(PATH, pattern='tmob(hspa|reg)_(firefox|chrome).*.pcap$')) {
  fn = unlist(strsplit(toString(filename), '(_)'))
  domain = paste(fn[2], fn[3], sep='_')
  if (!has.key(domain, h)) {
    h[[domain]] = list()
  }
  h[[domain]] = c(h[[domain]], c=filename)
}

for (key in keys(h)) {
  print(key)
  if (length(h[[key]]) < 2) {
    next
  }
  print(h[[key]][1])
  path1 = paste(PATH, h[[key]][1], sep='')
  path2 = paste(PATH, h[[key]][2], sep='')
  p1 = plot_convos(path1)
  p2 = plot_convos(path2)

  newfile = paste(PATH, key, sep='')
  outsvg = paste(newfile, 'svg', sep='.')

  svg(file=outsvg)
  cp = grid.arrange(p1, p2)
  dev.off()
  # ggsave(outsvg, cp)
}
