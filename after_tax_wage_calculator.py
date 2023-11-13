#! python3
# -*- coding: utf-8 -*-

import sys


class SocialInsurance:
    """
    五险
    """

    def __init__(self, lower_bound, upper_bound, ratio, coupon):
        """
        :param lower_bound: 缴费基数下限，inclusive
        :param upper_bound: 缴费基数上限，inclusive
        :param ratio: 缴费比例
        :param coupon: 其他扣除费用
        """
        self.min = lower_bound
        self.max = upper_bound
        self.ratio = ratio
        self.coupon = coupon


class HousingFund:
    """
    一金
    """

    def __init__(self, lower_bound, upper_bound, ratio, coupon):
        """
        :param lower_bound: 月缴存额下限，inclusive
        :param upper_bound: 月缴存额上限，inclusive
        :param ratio: 缴费比例
        :param coupon: 其他扣除费用
        """
        self.min = lower_bound
        self.max = upper_bound
        self.ratio = ratio
        self.coupon = coupon


class TaxableWageCalculator:
    # 社保
    # 数据来源：https://rsj.sh.gov.cn/tshbxjfjs_17348/20230829/t0035_1417934.html

    # 社保缴费基数
    SOCIAL_INSURANCE_LOWER_BOUND = 7310
    SOCIAL_INSURANCE_UPPER_BOUND = 36549

    # 社保个人缴费
    SOCIAL_INSURANCE_PERSONAL_PER_MONTH = [
        # 养老
        SocialInsurance(SOCIAL_INSURANCE_LOWER_BOUND, SOCIAL_INSURANCE_UPPER_BOUND,
                        0.08, 0),
        # 医疗
        SocialInsurance(SOCIAL_INSURANCE_LOWER_BOUND, SOCIAL_INSURANCE_UPPER_BOUND,
                        0.02, 0),
        # 失业
        SocialInsurance(SOCIAL_INSURANCE_LOWER_BOUND, SOCIAL_INSURANCE_UPPER_BOUND,
                        0.005, 0)
    ]
    SOCIAL_INSURANCE_PERSONAL = [SOCIAL_INSURANCE_PERSONAL_PER_MONTH] * 12

    # 社保单位缴费
    SOCIAL_INSURANCE_COMPANY_PER_MONTH = [
        # 养老
        SocialInsurance(SOCIAL_INSURANCE_LOWER_BOUND, SOCIAL_INSURANCE_UPPER_BOUND,
                        0.16, 0),
        # 医疗
        SocialInsurance(SOCIAL_INSURANCE_LOWER_BOUND, SOCIAL_INSURANCE_UPPER_BOUND,
                        0.10, 0),
        # 失业
        SocialInsurance(SOCIAL_INSURANCE_LOWER_BOUND, SOCIAL_INSURANCE_UPPER_BOUND,
                        0.005, 0),
        # 工伤（不明，暂时以最低档计算）
        SocialInsurance(SOCIAL_INSURANCE_LOWER_BOUND, SOCIAL_INSURANCE_UPPER_BOUND,
                        0.0016, 0)
    ]
    SOCIAL_INSURANCE_COMPANY = [SOCIAL_INSURANCE_COMPANY_PER_MONTH] * 12

    # 住房公积金
    # 数据来源：https://www.shgjj.com/html/newxxgk/zcwj/gfxwj/215343.html

    # 住房公积金限额
    # 此处为“各7%”档次
    HOUSING_FUND_LOWER_BOUND = 362.0 / 2
    HOUSING_FUND_UPPER_BOUND = 5116.0 / 2

    # 住房公积金个人缴费
    HOUSING_FUND_PERSONAL_PER_MONTH = HousingFund(HOUSING_FUND_LOWER_BOUND, HOUSING_FUND_UPPER_BOUND, 0.07, 0)
    HOUSING_FUND_PERSONAL = [HOUSING_FUND_PERSONAL_PER_MONTH] * 12

    # 住房公积金单位缴费
    HOUSING_FUND_COMPANY_PER_MONTH = HousingFund(HOUSING_FUND_LOWER_BOUND, HOUSING_FUND_UPPER_BOUND, 0.07, 0)
    HOUSING_FUND_COMPANY = [HOUSING_FUND_COMPANY_PER_MONTH] * 12

    @classmethod
    def get_taxable_wages(cls, gross_wages, social_insurance_bases, housing_fund_bases):
        """
        :param gross_wages: 税前工资
        :param social_insurance_bases: 五险缴费基数（默认与 gross_wages 一样）
        :param housing_fund_bases: 一金缴存基数（默认与 gross_wages 一样）
        :return: 应税收入
        """
        size = len(gross_wages)
        assert size == 12 and len(social_insurance_bases) == size and len(housing_fund_bases) == size
        taxable_wages = []
        for i in range(0, size):

            # 税前列支
            pre_tax_deduction_personal = 0

            # 五险
            social_insurance_base = social_insurance_bases[i]
            social_insurance_personal = cls.SOCIAL_INSURANCE_PERSONAL[i]
            for j in range(0, len(social_insurance_personal)):
                temp = social_insurance_base - social_insurance_personal[j].coupon
                if temp < social_insurance_personal[j].min:
                    temp = social_insurance_personal[j].min
                elif temp > social_insurance_personal[j].max:
                    temp = social_insurance_personal[j].max
                pre_tax_deduction_personal += temp * social_insurance_personal[j].ratio

            # 一金
            housing_fund_base = housing_fund_bases[i]
            housing_fund_personal = cls.HOUSING_FUND_PERSONAL[i]
            temp = housing_fund_base * housing_fund_personal.ratio
            if temp < housing_fund_personal.min:
                pre_tax_deduction_personal += housing_fund_personal.min
            elif temp > housing_fund_personal.max:
                pre_tax_deduction_personal += housing_fund_personal.max
            else:
                pre_tax_deduction_personal += temp

            gross_wage = gross_wages[i]
            if gross_wage - pre_tax_deduction_personal < 0:
                raise ValueError('gross_wage {} less than pre_tax_deduction_personal {}'
                                 .format(gross_wage, pre_tax_deduction_personal))
            taxable_wages.append(gross_wage - pre_tax_deduction_personal)
        return taxable_wages


class TaxRatio:
    def __init__(self, lower_bound, upper_bound, ratio, coupon):
        """
        :param lower_bound: 应纳税所得额下限，exclusive
        :param upper_bound: 应纳税所得额上限，inclusive
        :param ratio: 税率
        :param coupon: 速算扣除数
        """
        self.min = lower_bound
        self.max = upper_bound
        self.ratio = ratio
        self.coupon = coupon


class AfterTaxWageCalculator:
    # 个人所得税
    # 数据来源：http://shanghai.chinatax.gov.cn/zcfw/zcfgk/grsds/202302/t466009.html

    # “所得项目小类”为“正常工资薪金”的个人所得税税率表
    TAX_RATIO_PER_MONTH = [TaxRatio(0, 36000, 0.03, 0),
                           TaxRatio(36000, 144000, 0.1, 2520),
                           TaxRatio(144000, 300000, 0.2, 16920),
                           TaxRatio(300000, 420000, .25, 31920),
                           TaxRatio(420000, 660000, .3, 52920),
                           TaxRatio(660000, 960000, .35, 85920),
                           TaxRatio(960000, sys.maxsize, .45, 181920)]
    TAX_RATIO = [TAX_RATIO_PER_MONTH] * 12

    # 应税收入中，全月各项免税、减除、扣除费用（如减除费用、专项扣除等）
    WAGE_FREE_OF_TAX = [5000] * 12

    @classmethod
    def get_after_tax_wages(cls, taxable_wages, tax_bases):
        """
        :param taxable_wages: 应税收入
        :param tax_bases: 个人所得税实际缴税基数（默认与 taxable_wages 一样）
        :return: 税后工资
        """
        size = len(taxable_wages)
        assert size == 12 and len(tax_bases) == size
        after_tax_wages = []
        accumulated_taxable_wage = 0  # 累计收入
        accumulated_wage_free_of_tax = 0  # 累计各项免税、减除、扣除费用
        accumulated_tax_amount_paid = 0  # 累计已缴税额
        for i in range(0, size):

            # 累计收入与扣除详情
            tax_base = tax_bases[i]
            accumulated_taxable_wage += tax_base
            accumulated_wage_free_of_tax += cls.WAGE_FREE_OF_TAX[i]
            accumulated_net_taxable_wage = accumulated_taxable_wage - accumulated_wage_free_of_tax  # 累计应纳税所得额
            if accumulated_net_taxable_wage < 0:
                accumulated_net_taxable_wage = 0

            # 税款计算
            tax_ratio = cls.get_tax_ratio(i, accumulated_net_taxable_wage)
            ratio = tax_ratio.ratio  # 税率
            coupon = tax_ratio.coupon  # 速算扣除数
            accumulated_tax_amount_payable = accumulated_net_taxable_wage * ratio - coupon  # 累计应纳税额
            current_tax_amount = accumulated_tax_amount_payable - accumulated_tax_amount_paid  # 本期申报税额
            if current_tax_amount < 0:
                raise ValueError('month {} current_tax_amount {} less than 0'.format(i, current_tax_amount))

            taxable_wage = taxable_wages[i]
            after_tax_wages.append(taxable_wage - current_tax_amount)
            accumulated_tax_amount_paid = accumulated_tax_amount_payable
        return after_tax_wages

    @classmethod
    def get_tax_ratio(cls, month, net_taxable_wage):
        assert 0 <= month < 12
        for tax_ratio in cls.TAX_RATIO[month]:
            if tax_ratio.min < net_taxable_wage <= tax_ratio.max:
                return tax_ratio
        return TaxRatio(0, 0, 0, 0)


class SeparateAfterTaxWageCalculator:
    # 按月换算后的综合所得税率表
    # 数据来源：https://www.chinatax.gov.cn/n810341/n810755/c3978994/content.html
    # “所得项目小类”为“全年一次性奖金”的个人所得税税率表
    TAX_RATIO = [TaxRatio(0, 3000, 0.03, 0),
                 TaxRatio(3000, 12000, 0.1, 210),
                 TaxRatio(12000, 25000, 0.2, 1410),
                 TaxRatio(25000, 35000, .25, 2660),
                 TaxRatio(35000, 55000, .3, 4410),
                 TaxRatio(55000, 80000, .35, 7160),
                 TaxRatio(80000, sys.maxsize, .45, 15160)]

    @classmethod
    def get_after_tax_wage(cls, taxable_wage):
        """
        :param taxable_wage: “所得项目小类”为“全年一次性奖金”、单独计税方式计算的应税收入
        :return: 税后工资
        """
        tax_ratio = cls.get_tax_ratio(taxable_wage)
        tax_amount = taxable_wage * tax_ratio.ratio - tax_ratio.coupon
        return taxable_wage - tax_amount

    @classmethod
    def get_tax_ratio(cls, taxable_wage):
        taxable_wage_per_month = taxable_wage / 12
        for tax_ratio in cls.TAX_RATIO:
            if tax_ratio.min < taxable_wage_per_month <= tax_ratio.max:
                return tax_ratio
        return TaxRatio(0, 0, 0, 0)


if __name__ == '__main__':
    # 根据每月税前工资，计算税后工资
    print("--------根据每月税前工资，计算税后工资--------")
    gross_wage_per_month = 100_000_000  # 每月税前工资；一个小目标
    gross_wages = [gross_wage_per_month] * 12

    taxable_wages = TaxableWageCalculator.get_taxable_wages(gross_wages, gross_wages, gross_wages)
    print(f"taxable_wages: {taxable_wages}")

    after_tax_wages = AfterTaxWageCalculator.get_after_tax_wages(taxable_wages, taxable_wages)
    print(f"after_tax_wages: {after_tax_wages}")

    total_gross_wage = sum(gross_wages)
    total_taxable_wage = sum(taxable_wages)
    total_after_tax_wage = sum(after_tax_wages)
    total_tax = total_taxable_wage - total_after_tax_wage
    total_ratio = total_tax / total_after_tax_wage
    print(f"total_gross_wage: {total_gross_wage}")
    print(f"total_taxable_wage: {total_taxable_wage}")
    print(f"total_after_tax_wage: {total_after_tax_wage}")
    print(f"total_tax: {total_tax}")
    print(f"total_ratio: {total_ratio}")

    print(f"total_after_tax_wage add separate_after_tax_wage: "
          f"{total_after_tax_wage + SeparateAfterTaxWageCalculator.get_after_tax_wage(gross_wage_per_month * 7)}")

    # 根据年实际税后工资，二分查找税前工资
    # 假设以下计算方法符合二分查找的条件（具有二段性）
    # “全年一次性奖金”采用单独计税方式计算
    print("--------根据年实际税后工资，二分查找税前工资--------")
    lo = 0  # 每月税前工资下限
    hi = 100_000  # 每月税前工资上限
    actual_total_after_tax_wage = 1_000_000  # 年实际税后工资
    annual_one_time_bonus_multiplier = 1  # 全年一次性奖金 / 每月税前工资
    computed_gross_wage_per_month = 0
    computed_total_after_tax_wage = 0
    while lo < hi:
        computed_gross_wage_per_month = (hi - lo) / 2 + lo
        gross_wages = [computed_gross_wage_per_month] * 12
        taxable_wages = TaxableWageCalculator.get_taxable_wages(gross_wages, gross_wages, gross_wages)
        after_tax_wages = AfterTaxWageCalculator.get_after_tax_wages(taxable_wages, taxable_wages)
        computed_total_after_tax_wage = sum(after_tax_wages) + SeparateAfterTaxWageCalculator.get_after_tax_wage(
            computed_gross_wage_per_month * annual_one_time_bonus_multiplier)
        if computed_total_after_tax_wage < actual_total_after_tax_wage:
            lo += 1
        elif computed_total_after_tax_wage > actual_total_after_tax_wage:
            hi -= 1
        else:
            break
    print(f"computed_gross_wage_per_month: {computed_gross_wage_per_month}")
    print(f"computed_total_after_tax_wage: {computed_total_after_tax_wage}")
