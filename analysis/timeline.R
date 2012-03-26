require('hash')
require('ggplot2')
library(gridExtra)

# PATH = '/home/tierney/repos/web_perf/empirical/ec2_017/'

plot_convos = function(filename, max_time) {
  FLOWTIME = '/home/tierney/repos/web_perf/analysis/flowtime.rb'

  if (file.info(filename)[["size"]] == 0) {
    return()
  }

  data = read.csv(pipe(paste(FLOWTIME, filename)), header=T, sep=",")

  p = ggplot(data=data, aes(frame.time_relative, stream_id, color=direction)) +
    geom_point(aes(size = frame.len),
               position=position_jitter(width=0, height=0.2)) +
    scale_shape() +
    scale_x_continuous(limits=c(0,ceiling(max_time))) +
    scale_color_hue() +
    opts(title = basename(filename))
  out_svg = paste(filename, 'svg', sep='.')
  ggsave(out_svg)
  return(p)
}

for (filename in list.files(PATH, pattern='(firefox|chrome).*.pcap$')) {
 file_path = paste(PATH, filename, sep='')
 max_time = flow_max(file_path)
 
 plot_convos(file_path, max_time)
}

## h = hash()
## for (filename in list.files(PATH, pattern='tmob(hspa|reg)_(firefox|chrome).*.pcap$')) {
##   fn = unlist(strsplit(toString(filename), '(_)'))
##   domain = paste(fn[2], fn[3], sep='_')
##   if (!has.key(domain, h)) {
##     h[[domain]] = list()
##   }
##   h[[domain]] = c(h[[domain]], c=filename)
## }

## flow_max = function(pathname) {
##   FLOWTIME = '/home/tierney/repos/web_perf/analysis/flowtime.rb'
##   max_row = read.csv(pipe(paste(paste(FLOWTIME, pathname), '| tail -n 1')), header=FALSE, sep=',')
##   return(as.numeric(max_row[1]))
## }

## for (key in keys(h)) {
##   print(key)
##   if (length(h[[key]]) < 2) {
##     next
##   }
##   print(h[[key]][1])
##   path1 = paste(PATH, h[[key]][1], sep='')
##   path2 = paste(PATH, h[[key]][2], sep='')

##   if ((file.info(path1)[["size"]] == 0) || (file.info(path2)[['size']] == 0)) {
##     next
##   }

##   max1 = flow_max(path1)
##   max2 = flow_max(path2)
##   max_time = max(max1, max2)
##   print(paste('Max time found:', max_time))

##   p1 = plot_convos(path1, max_time)
##   p2 = plot_convos(path2, max_time)

##   newfile = paste(PATH, key, sep='')
##   outsvg = paste(newfile, 'svg', sep='.')

##   svg(file=outsvg, width=11, height=8.5)
##   cp = grid.arrange(p1, p2)
##   dev.off()
##   # ggsave(outsvg, cp)
## }
