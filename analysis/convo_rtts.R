# Notes:
## jpeg - inverse relationship (size, download time?)

# Signals and Stories.

require('ggplot2')
require('hash')
library(gridExtra)

increment <- function(x) {
  eval.parent(substitute(x <- x + 1))
}

data = read.csv('~/data.log', header=T, sep=',')

individual_plots = function(data) {
  for (pfilename in unique(data$filename)) {
    sdata = subset(data, filename == pfilename)
    q = qplot(reorder(type, rtt, min), rtt, data=sdata) +
      scale_x_discrete(name='') +
      scale_y_log10(name='RTT (log(ms))') +
      geom_boxplot() + 
      opts(axis.text.x=theme_text(angle=-90, hjust=0),
           title=pfilename)
    out_svg = paste(pfilename, 'svg', sep='.')
    ggsave(out_svg)
  }
}

# individual_plots(data)
View(data)
#show(q)

#qplot(length, rtt, data=data) + 
#  scale_y_continuous(name='RTT (sec)', limits=c(0.03,0.2), breaks=seq(0,0.25,0.01))

## for (line in lines) {
##   sline = unsplit(strsplit(line,','))
## }

## i = 0
## frames = list()
## max_val = 0
## for (line in lines) {
##   data = unlist(strsplit(line, ','))
##   name = data[1]
##   values = as.numeric(data[2:length(data)])
##   max_val = max(max_val, values)
##   frames[[name]] = data.frame(rtts=c(values))
## }

## medians = sapply(frames, function(f) { median(f[1,]) })
## oframes = frames[order(medians)]

## plots = list()
## p = ggplot()
## for (plotname in names(oframes)) {
##   plots[[plotname]] = ggplot(oframes[[plotname]], aes(plotname,rtts)) +
##     scale_x_discrete(name='', labels=plotname) +
##     scale_y_continuous(name='RTT (sec)', limits=c(0,max_val)) +
##     geom_boxplot()
##   show(plots[[plotname]])
## }

## do.call(grid.arrange, plots)
