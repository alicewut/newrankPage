from selenium import webdriver
from lxml import etree
import time
import pymysql
class NewrankWx(object):
	base_url = 'https://www.newrank.cn/public/info/list.html'
	driver = webdriver.Chrome()
	driver.maximize_window()
	driver.get(base_url)
	
	def __init__(self):
		self.db = pymysql.connect('192.168.12.139', 'alice', 'a11112222', 'image', charset='utf8')
		self.cursor = self.db.cursor()
		self.sql = 'INSERT INTO wxInfo(wxname, wxnumber) VALUES(%s, %s)'
		
	
	def operatePage(self):
		"""
		返回所有分类,作用于 day 与 week 爬取
		:return:
		"""
		return self.driver.find_elements_by_xpath('//div[@class="wx-right-type-list"]/div[contains(@class, "wx-right-type")]/a')
	
	def operateMonthPage(self):
		"""
		返回总排名对象
		:return:
		"""
		return self.driver.find_element_by_id('wx_month_all').click()
	

	def selectDate(self):
		"""
		显示日期范围选择框，并且下拉滚动条使窗口与当前元素处于同一位置，避免无法点击。选择日期，bing'jie
		:return:
		"""
		time_list = self.driver.find_elements_by_xpath('//ul[@class="lately lately_new"]/li/a')
		for index, timepoint in enumerate(time_list):
			# 显示下拉框
			self.driver.execute_script('document.getElementById("date_list").setAttribute("style","block");')
			
			# 向下拖动滚动条，使最下面a元素可见
			target = self.driver.find_element_by_xpath('//ul[@class="lately lately_new"]/li/a[last()]')
			self.driver.execute_script("arguments[0].scrollIntoView();", target)
			timepoint.click()
			
			# 选择框超出范围
			target_header = self.driver.find_element_by_id('txt_account')
			self.driver.execute_script("arguments[0].scrollIntoView();", target_header)
			time.sleep(1)
			yield self.driver.page_source
	

	def parsePage(self, html):
		"""
		解析网页源代码，通用
		:param html:传入网页源代码
		:return:
		"""
		html_obj = etree.HTML(html)
		td_List = html_obj.xpath('//div[@class="l_main wx_main"]/table[1]/following-sibling::table/tbody/tr/td[2]/div')
		for td in td_List:
			wxname = td.xpath('./h4/a[1]/text()')[0]
			wxnumber = td.xpath('./p/a/text()')[0]
			if wxname is not None and wxnumber is not None:
				yield (wxname, wxnumber)
	
	def clickDay(self):
		"""
		爬取日榜
		:return:
		"""
		target_header = self.driver.find_element_by_id('txt_account')
		self.driver.execute_script("arguments[0].scrollIntoView();", target_header)
		self.driver.find_element_by_id('day-bang').click()
		style_list = self.operatePage()
		for style in style_list:
			style.click()
			time.sleep(1)
			html_gen = self.selectDate()
			for html in html_gen:
				for item in self.parsePage(html):
					self.dbInsert(item)
	
	def clickWeek(self):
		"""
		爬取周榜
		:return:
		"""
		target_header = self.driver.find_element_by_id('txt_account')
		self.driver.execute_script("arguments[0].scrollIntoView();", target_header)
		self.driver.find_element_by_id('week-bang').click()
		style_list = self.operatePage()
		for style in style_list:
			style.click()
			time.sleep(1)
			html_gen = self.selectDate()
			for html in html_gen:
				for item in self.parsePage(html):
					self.dbInsert(item)
		
	def clickMonth(self):
		"""
		爬取月榜
		:return:
		"""
		target_header = self.driver.find_element_by_id('txt_account')
		self.driver.execute_script("arguments[0].scrollIntoView();", target_header)
		self.driver.find_element_by_id('month-bang').click()
		self.operateMonthPage()
		html_gen = self.selectDate()
		for html in html_gen:
			for item in self.parsePage(html):
				self.dbInsert(item)

	def dbInsert(self, item):
		try:
			self.cursor.execute(self.sql, item)
			self.db.commit()
		except:
			self.db.rollback()
			print("数据已存在，跳过当前数据")

if __name__ == '__main__':
	
	c = NewrankWx()
	c.clickMonth()
	c.clickDay()
	c.clickWeek()
	
	c.driver.close()
	c.db.close()

