# Notes:
## jpeg - inverse relationship (size, download time?)

require('ggplot2')
library(gridExtra)

increment <- function(x) {
  eval.parent(substitute(x <- x + 1))
}

lines = readLines('~/data.log')

i = 0
frames = list()
max_val = 0
for (line in lines) {
  data = unlist(strsplit(line, ','))
  name = data[1]
  values = as.numeric(data[2:length(data)])
  max_val = max(max_val, values)
  frames[[name]] = data.frame(rtts=c(values))
}
medians = sapply(frames, function(f) { median(f[1,]) })
oframes = frames[order(medians)]

plots = list()
p = ggplot()
for (plotname in names(oframes)) {
  plots[[plotname]] = ggplot(oframes[[plotname]], aes(plotname,rtts)) + 
    scale_x_discrete(name='', labels=plotname) +
    scale_y_continuous(name='RTT (sec)', limits=c(0,max_val)) +
    geom_boxplot()
  show(plots[[plotname]])
}

do.call(grid.arrange, plots)
